from django import template
from django.conf import settings
from urllib.parse import urlsplit, urlunsplit
import os

from wagtail.models import Locale as WagtailLocale
from blog.models import BlogIndexPage

register = template.Library()


@register.filter
def add_class(bound_field, css):
    attrs = bound_field.field.widget.attrs.copy()
    attrs["class"] = (attrs.get("class", "") + " " + css).strip()
    return bound_field.as_widget(attrs=attrs)


@register.filter
def basename(value):
    try:
        return os.path.basename(value)
    except Exception:
        return value


@register.simple_tag(takes_context=True)
def lang_path(context, lang_code):
    request = context["request"]
    parts = urlsplit(request.get_full_path())
    path = parts.path

    langs = [code.split("-")[0] for code, _ in settings.LANGUAGES]
    for code in langs:
        pref = f"/{code}/"
        if path.startswith(pref):
            path = "/" + path[len(pref):]
            break

    default = settings.LANGUAGE_CODE.split("-")[0]
    target = lang_code.split("-")[0]

    if target == default:
        new_path = path
    else:
        new_path = f"/{target}{path}"

    return urlunsplit(("", "", new_path, parts.query, parts.fragment))


@register.simple_tag(takes_context=True)
def blog_index_url(context):
    request = context.get('request')
    page = BlogIndexPage.objects.first()
    if not page:
        return '/'

    from urllib.parse import urlsplit, urlunsplit
    try:
        current_lang = (getattr(request, 'LANGUAGE_CODE', '') or '').split('-')[0]
        default = settings.LANGUAGE_CODE.split('-')[0]

        try:
            locale = WagtailLocale.objects.get(language_code=current_lang)
            translated = page.get_translation_or_none(locale)
        except Exception:
            translated = None

        base_url = (translated or page).get_url(request)

        parts = urlsplit(base_url)
        path = parts.path

        langs = [code.split('-')[0] for code, _ in settings.LANGUAGES]
        for code in langs:
            pref = f'/{code}/'
            if path.startswith(pref):
                path = '/' + path[len(pref):]
                break

        if current_lang != default:
            path = f'/{current_lang}{path}'

        return urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))
    except Exception:
        return page.get_url(request) if request else page.url
