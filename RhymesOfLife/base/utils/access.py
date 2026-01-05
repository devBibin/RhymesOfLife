from django.contrib.auth import get_user_model

from ..models import AdditionalUserInfo, PatientAccessRequest

User = get_user_model()


def _get_user_info(user) -> AdditionalUserInfo | None:
    if not user or not getattr(user, "is_authenticated", False):
        return None
    return getattr(user, "additional_info", None)


def is_external_doctor(user) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return user.groups.filter(name="external_doctor").exists()


def has_patient_access(user, patient_info: AdditionalUserInfo) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser or user.is_staff or user.has_perm("base.view_patient_exams"):
        return True
    doctor_info = _get_user_info(user)
    if not doctor_info or not patient_info:
        return False
    return PatientAccessRequest.objects.filter(
        doctor=doctor_info,
        patient=patient_info,
        status=PatientAccessRequest.Status.APPROVED,
    ).exists()


def get_access_status_map(doctor_info: AdditionalUserInfo, patient_ids: list[int]) -> dict[int, str]:
    if not doctor_info or not patient_ids:
        return {}
    qs = PatientAccessRequest.objects.filter(doctor=doctor_info, patient_id__in=patient_ids)
    return {r.patient_id: r.status for r in qs}
