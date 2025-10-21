from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.utils.translation import gettext_lazy as _

ALLOWED_URL_NAMES_FOR_BANNED = {
    "banned",
    "logout",
    "login",
    "admin:logout",
}


class BannedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None

        info = getattr(user, "additional_info", None)
        if not info or not info.is_banned:
            return None

        try:
            match = resolve(request.path_info)
            url_name = match.view_name
        except Exception:
            url_name = ""

        if url_name in ALLOWED_URL_NAMES_FOR_BANNED or request.path_info.startswith(("/static/", "/media/")):
            return None

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"detail": str(_("Your account is banned."))}, status=403)

        return redirect("banned")
