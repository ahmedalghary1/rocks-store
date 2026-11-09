from django.http import JsonResponse
from django.views.csrf import csrf_failure as default_csrf_failure
from django.views.decorators.cache import never_cache


@never_cache
def csrf_failure(request, reason=""):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "ok": False,
            "code": "csrf_failed",
            "message": "Please reload the page and try again.",
        }, status=403)
    return default_csrf_failure(request, reason=reason)
