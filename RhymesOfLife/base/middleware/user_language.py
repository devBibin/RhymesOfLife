from django.utils import translation

SESSION_KEY = "user_lang"


class SetUserLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            lang = request.session.get(SESSION_KEY)
            if not lang:
                info = getattr(user, "additional_info", None)
                lang = getattr(info, "language", None) or "ru"
                request.session[SESSION_KEY] = lang
            translation.activate(lang)
            request.LANGUAGE_CODE = lang
        return self.get_response(request)
