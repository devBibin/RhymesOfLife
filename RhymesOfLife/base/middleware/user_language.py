from django.conf import settings
from django.utils import translation

try:
    from django.utils.translation import LANGUAGE_SESSION_KEY as LANG_SESSION_KEY
except Exception:
    LANG_SESSION_KEY = "django_language"


class SetUserLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin/"):
            with translation.override("en"):
                return self.get_response(request)
        if request.path.startswith("/cms/"):
            with translation.override("en"):
                return self.get_response(request)

        lang = None
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            info = getattr(user, "additional_info", None)
            lang = getattr(info, "language", None)

        if not lang:
            lang = request.session.get(LANG_SESSION_KEY) or request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)

        lang = lang or settings.LANGUAGE_CODE
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        response = self.get_response(request)

        if hasattr(request, "session"):
            request.session[LANG_SESSION_KEY] = lang
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang, samesite="Lax")

        translation.deactivate()
        return response
