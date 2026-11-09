import hashlib
import logging
import secrets
import time
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.middleware.locale import LocaleMiddleware
from django.utils import translation
from django.utils.cache import patch_vary_headers
from .translations import translate_markup


class DefaultEnglishLocaleMiddleware(LocaleMiddleware):
    """Serve stable English/Arabic public URLs and cookie-localized checkout."""

    def process_request(self, request):
        language = translation.get_language_from_path(request.path_info)
        if not language:
            # Public URLs have a stable language even when cookies differ.
            private = request.path.startswith(("/cart/", "/checkout/", "/account/", "/auth/", "/dashboard/", "/admin/", "/api/"))
            if request.path.startswith("/api/"):
                lang_param = request.GET.get("lang") or request.headers.get("Accept-Language", "").split(",")[0].split("-")[0].strip().lower()
                language = lang_param if lang_param in {"ar", "en"} else request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME, settings.LANGUAGE_CODE)
            else:
                language = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME, settings.LANGUAGE_CODE) if private else settings.LANGUAGE_CODE
        supported = {code for code, _name in settings.LANGUAGES}
        if language not in supported:
            language = settings.LANGUAGE_CODE
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()

    def process_response(self, request, response):
        # Both languages are discoverable without cookies or Accept-Language.
        response.setdefault("Content-Language", request.LANGUAGE_CODE)
        patch_vary_headers(response, ("Cookie",))
        return response


class SecurityHeadersMiddleware:
    """Small, dependency-free baseline for browser security headers."""

    private_prefixes = ("/admin/", "/dashboard/", "/cart/", "/checkout/", "/account/", "/auth/", "/wishlist/", "/health/", "/api/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.csp_nonce = secrets.token_urlsafe(18)
        response = self.get_response(request)
        docs_page = request.path in {"/api/docs/", "/api/redoc/"}
        script_sources = ("'self' 'unsafe-inline' https://cdn.jsdelivr.net" if docs_page
                          else f"'self' 'nonce-{request.csp_nonce}'")
        style_sources = ("'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net" if docs_page
                         else "'self' 'unsafe-inline' https://fonts.googleapis.com")
        response.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            f"script-src {script_sources}; "
            f"style-src {style_sources}; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
        )
        response.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
        response.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        public_path = request.path.removeprefix("/ar") if request.path.startswith("/ar/") else request.path
        if public_path.startswith(self.private_prefixes) or public_path.startswith("/products/search/") or "/quick-view/" in public_path or response.status_code >= 400:
            response.setdefault("X-Robots-Tag", "noindex, nofollow, noarchive")
        return response


class SensitivePostRateLimitMiddleware:
    protected_paths = {
        "/admin/login/", "/auth/login/", "/account/register/", "/auth/password_reset/",
        "/api/v1/auth/register/", "/api/v1/auth/token/", "/api/v1/auth/token/refresh/",
        "/api/v1/orders/track/",
    }
    limit = 5
    window = 60

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "POST" and request.path in self.protected_paths:
            identity = request.META.get("REMOTE_ADDR", "unknown")
            if settings.TRUST_PROXY_HEADERS:
                forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
                if forwarded:
                    identity = forwarded.split(",", 1)[0].strip()
            digest = hashlib.sha256(f"{request.path}:{identity}".encode()).hexdigest()[:24]
            key = f"sensitive-post:{digest}"
            attempts = cache.get(key, 0)
            if attempts >= self.limit:
                message = "محاولات كثيرة. يرجى الانتظار دقيقة ثم المحاولة مرة أخرى." if request.path.startswith("/admin/") else "Too many attempts. Please wait one minute and try again."
                response = HttpResponse(message, status=429)
                response["Retry-After"] = str(self.window)
                return response
            if not cache.add(key, 1, self.window):
                try:
                    cache.incr(key)
                except ValueError:
                    cache.set(key, 1, self.window)
        return self.get_response(request)


class ArabicAdminLocaleMiddleware:
    """Keep the management dashboard Arabic without changing the public storefront language."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin/"):
            with translation.override("ar"):
                return self.get_response(request)
        return self.get_response(request)


class StorefrontTranslationMiddleware:
    """Translate public HTML and JSON while preserving stable storefront URLs."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Session bootstrap contains opaque CSRF tokens, never display copy.
        if request.path.startswith(("/admin/", "/dashboard/", "/api/", "/cart/session/")):
            return response
        content_type = response.get("Content-Type", "")
        if not (content_type.startswith("text/html") or content_type.startswith("application/json")):
            return response
        patch_vary_headers(response, ("Cookie",))
        if translation.get_language() != "ar":
            return response
        if getattr(response, "streaming", False) or response.has_header("Content-Encoding"):
            return response
        charset = response.charset or "utf-8"
        response.content = translate_markup(response.content.decode(charset)).encode(charset)
        if response.has_header("Content-Length"):
            response["Content-Length"] = str(len(response.content))
        return response


class TrafficTrackingMiddleware:
    """
    Safely logs visitor requests, differentiating
    authenticated users, guest visitors, and automated search engine bots.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger("traffic")

    def __call__(self, request):
        from core.traffic_tracker import (
            determine_path_type,
            get_client_ip,
            get_or_create_visitor_id,
            parse_user_agent,
            should_ignore_request,
        )

        if should_ignore_request(request):
            return self.get_response(request)

        start_time = time.perf_counter()
        visitor_id, is_new_vid = get_or_create_visitor_id(request)
        request.visitor_id = visitor_id

        response = self.get_response(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Attach cookie for tracking unique visitors across pages
        if is_new_vid:
            response.set_cookie(
                "rocks_vid",
                visitor_id,
                max_age=365 * 24 * 60 * 60,
                httponly=True,
                samesite="Lax",
            )

        try:
            from core.models import VisitLog

            user_agent = request.META.get("HTTP_USER_AGENT", "")
            ua_info = parse_user_agent(user_agent)
            user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
            is_authenticated = bool(user)

            raw_path = request.path_info or request.path or "/"

            VisitLog.objects.create(
                ip_address=get_client_ip(request),
                visitor_id=visitor_id,
                user=user,
                is_authenticated=is_authenticated,
                path=raw_path[:500],
                method=request.method[:10],
                status_code=response.status_code,
                referer=(request.META.get("HTTP_REFERER", ""))[:500],
                query_string=(request.META.get("QUERY_STRING", ""))[:500],
                is_bot=ua_info["is_bot"],
                bot_name=ua_info["bot_name"],
                device_type=ua_info["device_type"],
                browser=ua_info["browser"],
                browser_version=ua_info["browser_version"],
                os=ua_info["os"],
                user_agent=user_agent[:1000],
                path_type=determine_path_type(raw_path),
                response_time_ms=duration_ms,
            )
        except Exception:
            self.logger.debug("Visit logging skipped due to error", exc_info=True)

        return response

