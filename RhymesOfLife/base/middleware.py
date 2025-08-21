from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import resolve
from django.conf import settings
from .utils.logging import get_security_logger

seclog = get_security_logger()


class EnforceVerifiedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_names = set(getattr(settings, "EMAIL_VERIFICATION_EXEMPT_URLNAMES", set()))
        self.exempt_paths = set(getattr(settings, "EMAIL_VERIFICATION_EXEMPT_PATHS", set()))

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_superuser:
            info = getattr(request.user, "additional_info", None)
            if info and not info.is_verified:
                try:
                    match = resolve(request.path_info)
                    name = match.url_name
                except Exception:
                    name = None
                if request.path in self.exempt_paths or name in self.exempt_names:
                    return self.get_response(request)
                seclog.info("Blocked unverified access: user_id=%s path=%s", request.user.id, request.path)
                return redirect("verify_prompt")
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None
        if user.is_superuser:
            return None

        info = getattr(user, "additional_info", None)
        if not info or info.is_verified:
            return None

        path = request.path
        if any(path.startswith(p) for p in self._default_exempt_paths()):
            return None
        if any(path.startswith(p) for p in self.exempt_paths):
            return None

        try:
            match = resolve(path)
            name = match.url_name or ""
        except Exception:
            name = ""

        if name in self._default_exempt_names() or name in self.exempt_names:
            return None

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"detail": _("Email not verified.")}, status=403)

        return redirect("verify_prompt")

    @staticmethod
    def _default_exempt_paths():
        from django.conf import settings as dj_settings
        return [
            getattr(dj_settings, "STATIC_URL", "/static/"),
            getattr(dj_settings, "MEDIA_URL", "/media/"),
            "/favicon.ico",
            "/robots.txt",
        ]

    @staticmethod
    def _default_exempt_names():
        return {
            "login",
            "logout",
            "register",
            "home",
            "verify_email",
            "request_verification",
            "verify_prompt",
            "profile_onboarding",
            "set_language",
            "admin:index",
        }
