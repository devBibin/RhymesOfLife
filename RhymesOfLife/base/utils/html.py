from __future__ import annotations

from html import unescape
import re

import bleach
from bleach.css_sanitizer import CSSSanitizer


ALLOWED_TAGS = [
    "p", "br", "strong", "em", "u", "s", "span", "a", "ul", "ol", "li", "blockquote", "code", "pre", "hr",
    "h2", "h3", "h4", "h5", "h6", "figure", "figcaption", "img",
    "table", "thead", "tbody", "tr", "th", "td",
]
ALLOWED_ATTRS = {
    "*": ["class", "style"],
    "a": ["href", "title", "rel", "target"],
    "img": ["src", "alt", "width", "height", "loading", "class", "style"],
    "table": ["border", "style"],
    "th": ["colspan", "rowspan", "style"],
    "td": ["colspan", "rowspan", "style"],
}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]
ALLOWED_CSS_PROPERTIES = [
    "color",
    "background-color",
    "font-size",
    "font-family",
    "text-align",
    "text-decoration",
    "font-weight",
    "font-style",
]
CSS_SANITIZER = CSSSanitizer(allowed_css_properties=ALLOWED_CSS_PROPERTIES)


def sanitize_html(html: str) -> str:
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        protocols=ALLOWED_PROTOCOLS,
        css_sanitizer=CSS_SANITIZER,
        strip=True,
    )


def is_empty_html(html: str) -> bool:
    text = re.sub(r"<[^>]+>", " ", html or "")
    text = unescape(text).replace("\xa0", " ").strip()
    return not text
