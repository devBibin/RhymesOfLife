from __future__ import annotations

import re

from django import template
from django.template.defaultfilters import linebreaksbr
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from base.utils.html import sanitize_html


register = template.Library()

HTML_TAG_RE = re.compile(r"</?[a-zA-Z][^>]*>")


@register.filter(name="render_post_content")
def render_post_content(value):
    text = str(value or "")
    if not text:
        return ""
    if HTML_TAG_RE.search(text):
        return mark_safe(sanitize_html(text))
    return linebreaksbr(conditional_escape(text))
