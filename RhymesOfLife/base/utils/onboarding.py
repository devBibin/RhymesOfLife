from __future__ import annotations
from django.urls import reverse


def has_consents(info) -> bool:
    return bool(info.tos_accepted and info.privacy_accepted and info.data_processing_accepted)


def is_profile_complete(info) -> bool:
    return bool(info.first_name and info.last_name and info.email and info.birth_date)


def next_onboarding_url(request) -> str | None:
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated or user.is_superuser:
        return None
    info = getattr(user, "additional_info", None)
    if not info:
        return reverse("verify_prompt")
    if not info.is_verified:
        return reverse("verify_prompt")
    if not getattr(info, "phone_verified", False):
        return reverse("connect_telegram")
    if not has_consents(info):
        return reverse("consents")
    if not is_profile_complete(info):
        return reverse("profile_edit")
    return None
