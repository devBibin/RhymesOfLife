import re
import requests
from django.conf import settings

INIT_URL = getattr(settings, "ZVONOK_API_INITIATE_URL", "")
POLL_URL = getattr(settings, "ZVONOK_API_POLLING_URL", "")
PUBLIC_KEY = getattr(settings, "PUBLIC_KEY_CALL", "")
CAMPAIGN_ID = getattr(settings, "CAMPAIGN_ID", "")
STATIC_GATEWAY = getattr(settings, "ZVONOK_STATIC_GATEWAY", "")


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
        r = requests.post(INIT_URL, data=payload, timeout=15, headers={"Accept": "application/json"})
        r.raise_for_status()
        data = _json(r)
        call_number = (
            data.get("call_number")
            or data.get("gateway_number")
            or data.get("phone_number")
            or STATIC_GATEWAY
        )
        return {"ok": True, "call_number": call_number, "provider_raw": data}
    except requests.HTTPError as e:
        return {"ok": False, "message": f"{e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"ok": False, "message": str(e)}


def poll_zvonok_status(phone: str):
    if not POLL_URL or not PUBLIC_KEY:
        return {"ok": False, "message": "Zvonok settings missing"}

    phone_api = normalize_phone_e164_no_plus(phone)
    params = {
        "public_key": PUBLIC_KEY,
        "campaign_id": CAMPAIGN_ID,
        "phone": phone_api,
    }
    try:
        r = requests.get(POLL_URL, params=params, timeout=15, headers={"Accept": "application/json"})
        r.raise_for_status()
        data = _json(r)
        raw_status = data.get("dial_status_display") or data.get("dial_status") or ""
        s = str(raw_status).strip().lower()
        verified = s in {"абонент ответил", "answered", "answered_call", "success"}
        return {"ok": True, "verified": verified, "dial_status_display": raw_status, "provider_raw": data}
    except requests.HTTPError as e:
        return {"ok": False, "message": f"{e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"ok": False, "message": str(e)}
