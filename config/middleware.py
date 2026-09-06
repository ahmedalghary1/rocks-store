import secrets
import hashlib
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.middleware.locale import LocaleMiddleware
from django.utils import translation
from django.utils.cache import patch_vary_headers
from .translations import translate_markup


class DefaultEnglishLocaleMiddleware(LocaleMiddleware):
    """Use English on a visitor's first request; honor an explicit language cookie."""

    def process_request(self, request):
        language = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME, settings.LANGUAGE_CODE)
        supported = {code for code, _name in settings.LANGUAGES}
        if language not in supported:
            language = settings.LANGUAGE_CODE
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()


class SecurityHeadersMiddleware:
    """Small, dependency-free baseline for browser security headers."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.csp_nonce = secrets.token_urlsafe(18)
        response = self.get_response(request)
        response.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            f"script-src 'self' 'nonce-{request.csp_nonce}'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
        )
        response.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
        response.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        return response


class SensitivePostRateLimitMiddleware:
    protected_paths = {"/admin/login/", "/auth/login/", "/account/register/", "/auth/password_reset/"}
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
        if request.path.startswith("/admin/"):
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
