from django import template
from django.templatetags.static import static

register = template.Library()


def _get_avatar_field(obj):
    f = getattr(obj, "avatar", None)
    if not f:
        ai = getattr(obj, "additional_info", None)
        if ai:
            f = getattr(ai, "avatar", None)
    return f


@register.simple_tag
def avatar_url(obj):
    f = _get_avatar_field(obj)
    try:
        if f and getattr(f, "name", None) and getattr(f, "storage", None) and f.storage.exists(f.name):
            return f.url
    except Exception:
        pass
    return static("images/default-avatar.png")
