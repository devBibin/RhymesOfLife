from __future__ import annotations
from typing import Iterable
from django.conf import settings
from django.urls import reverse


def _required_profile_fields() -> Iterable[str]:
    return getattr(
        settings,
        "ONBOARDING_REQUIRED_PROFILE_FIELDS",
        ("first_name", "last_name", "email", "birth_date"),
    )


def has_consents(info) -> bool:
    if not getattr(settings, "ONBOARDING_REQUIRE_CONSENTS", True):
        return True
    return bool(getattr(info, "tos_accepted", False)
                and getattr(info, "privacy_accepted", False)
                and getattr(info, "data_processing_accepted", False))


def is_profile_complete(info) -> bool:
    for f in _required_profile_fields():
        if not getattr(info, f, None):
            return False
    return True


def is_phone_ok(info) -> bool:
    if not getattr(settings, "ONBOARDING_REQUIRE_PHONE", True):
        return True
    return bool(getattr(info, "phone_verified", False))


def next_onboarding_url(request) -> str | None:
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser or (getattr(user, "is_staff", False) and getattr(settings, "ONBOARDING_SKIP_FOR_STAFF", True)):
        return None

    info = getattr(user, "additional_info", None)
    if not info or not getattr(info, "is_verified", False):
        return reverse("verify_prompt")
    if not is_phone_ok(info):
        return reverse("connect_telegram")
    if not has_consents(info):
        return reverse("consents")
    if not is_profile_complete(info):
        return reverse("profile_edit")
    return None
