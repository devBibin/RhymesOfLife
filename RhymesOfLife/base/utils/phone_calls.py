import re
import requests
from requests.adapters import HTTPAdapter, Retry
from django.conf import settings

INIT_URL = getattr(settings, "ZVONOK_API_INITIATE_URL", "")
POLL_URL = getattr(settings, "ZVONOK_API_POLLING_URL", "")
PUBLIC_KEY = getattr(settings, "PUBLIC_KEY_CALL", "")
CAMPAIGN_ID = getattr(settings, "CAMPAIGN_ID", "")
STATIC_GATEWAY = getattr(settings, "ZVONOK_STATIC_GATEWAY", "")


def _session():
    retries = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.7,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "POST"]),
    )
    s = requests.Session()
    s.mount("http://", HTTPAdapter(max_retries=retries))
    s.mount("https://", HTTPAdapter(max_retries=retries))
    return s


def normalize_phone_e164_no_plus(phone: str) -> str:
    digits = re.sub(r"\D+", "", phone or "")
    if not digits:
        return ""
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    if digits.startswith("9") and len(digits) == 10:
        digits = "7" + digits
    return digits


def normalize_phone_e164_with_plus(phone: str) -> str:
    d = normalize_phone_e164_no_plus(phone)
    return f"+{d}" if d else ""


def _json(resp):
    try:
        data = resp.json()
        if isinstance(data, list):
            return (data[0] if data else {}) or {}
        return data or {}
    except Exception:
        return {}


_VERIFIED_MARKERS = {
    "answered", "answered_call", "success", "completed",
    "абонент ответил", "успешно", "дозвон", "соединен"
}
_PENDING_MARKERS = {
    "calling", "ringing", "in_progress", "queued",
    "звонок", "ожидание", "выполняется", "набор"
}
_FAILED_MARKERS = {
    "no_answer", "failed", "busy", "cancelled", "not_allowed",
    "отклонен", "занято", "не дозвонились", "ошибка"
}


def initiate_zvonok_verification(phone: str, pincode: str):
    if not INIT_URL or not PUBLIC_KEY or not CAMPAIGN_ID:
        return {"ok": False, "message": "Zvonok settings missing"}

    phone_api = normalize_phone_e164_no_plus(phone)
    payload = {
        "public_key": PUBLIC_KEY,
        "campaign_id": CAMPAIGN_ID,
        "phone": phone_api,
        "pincode": str(pincode),
    }
    try:
        s = _session()
        r = s.post(INIT_URL, data=payload, timeout=15, headers={"Accept": "application/json"})
        r.raise_for_status()
        data = _json(r)

        tracking_id = (
            data.get("request_id")
            or data.get("call_id")
            or data.get("id")
            or data.get("task_id")
            or ""
        )

        call_number = (
            data.get("call_number")
            or data.get("gateway_number")
            or data.get("phone_number")
            or STATIC_GATEWAY
        )
        return {"ok": True, "call_number": call_number, "tracking_id": tracking_id, "provider_raw": data}
    except requests.HTTPError as e:
        return {"ok": False, "message": f"{e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"ok": False, "message": str(e)}


def poll_zvonok_status(phone: str, tracking_id: str | None = None):
    if not POLL_URL or not PUBLIC_KEY:
        return {"ok": False, "message": "Zvonok settings missing"}

    phone_api = normalize_phone_e164_no_plus(phone)
    params = {
        "public_key": PUBLIC_KEY,
        "campaign_id": CAMPAIGN_ID,
        "phone": phone_api,
    }
    if tracking_id:
        params["request_id"] = tracking_id
        params["call_id"] = tracking_id

    try:
        s = _session()
        r = s.get(POLL_URL, params=params, timeout=15, headers={"Accept": "application/json"})
        r.raise_for_status()
        data = _json(r)

        raw_status = (
            data.get("dial_status_display")
            or data.get("dial_status")
            or data.get("status")
            or data.get("call_status")
            or ""
        )
        s_l = str(raw_status).strip().lower()

        if s_l in _VERIFIED_MARKERS:
            return {"ok": True, "verified": True, "dial_status_display": raw_status, "provider_raw": data}
        if s_l in _FAILED_MARKERS:
            return {"ok": True, "verified": False, "failed": True, "dial_status_display": raw_status, "provider_raw": data}
        if s_l in _PENDING_MARKERS or not s_l:
            return {"ok": True, "verified": False, "dial_status_display": raw_status, "provider_raw": data}

        return {"ok": True, "verified": False, "dial_status_display": raw_status, "provider_raw": data}
    except requests.HTTPError as e:
        return {"ok": False, "message": f"{e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"ok": False, "message": str(e)}
