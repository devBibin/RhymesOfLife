from __future__ import annotations
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import resolve, Resolver404
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from base.utils.logging import get_security_logger
from base.utils.onboarding import next_onboarding_url

seclog = get_security_logger()


class EnforceOnboardingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_names = set(getattr(settings, "ONBOARDING_EXEMPT_URLNAMES", set()))
        self.exempt_paths = set(getattr(settings, "ONBOARDING_EXEMPT_PATHS", set()))

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None
        if user.is_superuser or (getattr(user, "is_staff", False) and getattr(settings, "ONBOARDING_SKIP_FOR_STAFF", True)):
            return None

        path = request.path
        if self._is_path_exempt(path):
            return None

        try:
            match = resolve(path)
            name = match.url_name or ""
        except Resolver404:
            name = ""

        if self._is_name_exempt(name):
            return None

        nxt = next_onboarding_url(request)
        if not nxt:
            return None

        if self._wants_json(request):
            seclog.info("Blocked not-onboarded JSON: user_id=%s path=%s next=%s", user.id, path, nxt)
            return JsonResponse({"detail": _("Complete onboarding."), "next": nxt}, status=412)

        seclog.info("Blocked not-onboarded access: user_id=%s path=%s next=%s", user.id, path, nxt)
        return redirect(nxt)

    def _is_path_exempt(self, path: str) -> bool:
        for p in self._default_exempt_paths():
            if path.startswith(p):
                return True
        for p in self.exempt_paths:
            if path.startswith(p):
                return True
        return False

    def _is_name_exempt(self, name: str) -> bool:
        return name in self._default_exempt_names() or name in self.exempt_names

    @staticmethod
    def _default_exempt_paths():
        static_url = getattr(settings, "STATIC_URL", "/static/")
        media_url = getattr(settings, "MEDIA_URL", "/media/")
        extra = getattr(settings, "ONBOARDING_DEFAULT_EXEMPT_PATHS_EXTRA", [])
        return [static_url, media_url, "/favicon.ico", "/robots.txt", "/jsi18n/", "/admin/jsi18n/"] + list(extra)

    @staticmethod
    def _default_exempt_names():
        return {
            "home",
            "home_public",
            "login",
            "logout",
            "register",
            "verify_email",
            "request_verification",
            "verify_prompt",
            "connect_telegram",
            "phone_enter",
            "phone_wait",
            "phone_status_api",
            "phone_change",
            "consents",
            "profile_edit",
            "my_profile",
            "user_profile",
            "set_language",
            "javascript-catalog",
            "admin:jsi18n",
            "admin:index",
        }

    @staticmethod
    def _wants_json(request) -> bool:
        if request.headers.get("X-Requested-With", "").lower() == "xmlhttprequest":
            return True
        accept = request.headers.get("Accept", "")
        if "application/json" in accept or "text/json" in accept:
            return True
        if request.path.startswith("/api/"):
            return True
        return False
