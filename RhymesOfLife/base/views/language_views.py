from django.shortcuts import redirect
from django.http import HttpResponseBadRequest
from django.conf import settings
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.utils.http import url_has_allowed_host_and_scheme

from base.models import AdditionalUserInfo

try:
    from django.utils.translation import LANGUAGE_SESSION_KEY as LANG_SESSION_KEY
except Exception:
    LANG_SESSION_KEY = "django_language"


def _safe_next_url(request):
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"
    if url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return "/"


@require_POST
@csrf_protect
def set_language(request):
    lang = request.POST.get("language") or request.POST.get("lang")
    allowed = {code for code, _ in settings.LANGUAGES}
    if lang not in allowed:
        return HttpResponseBadRequest(_("Invalid language"))

    if request.user.is_authenticated:
        info, _ = AdditionalUserInfo.objects.get_or_create(
            user=request.user, defaults={"language": lang}
        )
        if info.language != lang:
            info.language = lang
            info.save(update_fields=["language"])

    translation.activate(lang)
    request.LANGUAGE_CODE = lang
    request.session[LANG_SESSION_KEY] = lang

    response = redirect(_safe_next_url(request))
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang, samesite="Lax")
    return response
