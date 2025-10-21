from typing import Tuple
from django.core.cache import cache
from base.models import Config

KEY = "BLOG_MODERATION"
CACHE_KEY = "BLOG_MODERATION_CACHE"
DEFAULT = {"mode": "censored", "report_threshold": 5}


def get_moderation_config() -> Tuple[str, int]:
    cached = cache.get(CACHE_KEY)
    if cached:
        return cached["mode"], int(cached["report_threshold"])
    row = Config.objects.filter(key=KEY).values_list("value", flat=True).first() or {}
    mode = row.get("mode", DEFAULT["mode"])
    thr = int(row.get("report_threshold", DEFAULT["report_threshold"]))
    conf = {"mode": mode, "report_threshold": thr}
    cache.set(CACHE_KEY, conf, 60)
    return mode, thr


def set_moderation_config(mode: str, threshold: int):
    mode = mode if mode in ("censored", "uncensored") else "censored"
    threshold = max(1, int(threshold or 1))
    Config.objects.update_or_create(key=KEY, defaults={"value": {"mode": mode, "report_threshold": threshold}})
    cache.delete(CACHE_KEY)
