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
    request = context.get("request")
    if not request:
        return "/"
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
    new_path = path if target == default else f"/{target}{path}"
    return urlunsplit(("", "", new_path, parts.query, parts.fragment))


@register.simple_tag(takes_context=True)
def blog_index_url(context):
    request = context.get("request")
    page = BlogIndexPage.objects.first()
    if not page:
        return "/"
    try:
        return page.get_url(request) if request else page.url
    except Exception:
        return "/"


@register.filter
def is_following(current_info, target_info):
    try:
        if not current_info or not target_info:
            return False
        return current_info.is_following(target_info)
    except Exception:
        return False


@register.filter
def call_method(bound_method, arg):
    try:
        if callable(bound_method):
            return bound_method(arg)
        return False
    except Exception:
        return False


@register.filter
def get_item(d, key):
    return d.get(key, [])
