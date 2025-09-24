from django.shortcuts import redirect
from django.http import HttpResponseBadRequest
from django.conf import settings
from django.utils import translation
from base.models import AdditionalUserInfo


def set_language(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    lang = request.POST.get("language") or request.POST.get("lang")
    allowed = {code for code, _ in settings.LANGUAGES}
    if lang not in allowed:
        return HttpResponseBadRequest("Invalid language")
    if request.user.is_authenticated:
        info, _ = AdditionalUserInfo.objects.get_or_create(user=request.user, defaults={"language": lang})
        if info.language != lang:
            info.language = lang
            info.save(update_fields=["language"])
        request.session["user_lang"] = lang
    translation.activate(lang)
    request.LANGUAGE_CODE = lang
    next_url = request.POST.get("next") or "/"
    return redirect(next_url)
