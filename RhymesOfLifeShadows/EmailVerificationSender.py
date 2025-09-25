from urllib.parse import urljoin
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.conf import settings
from django.utils.translation import gettext as _


class EmailVerificationSender:
    PROVIDERS = {"mailgun": "_send_via_mailgun"}

    def __init__(self, provider: str = "mailgun", logger=None):
        self.provider = provider
        self.logger = logger or self._default_logger()
        self.session = self._build_session()

    def _default_logger(self):
        import logging
        return logging.getLogger(__name__)

    def _build_session(self) -> requests.Session:
        s = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("POST",),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
        s.mount("https://", adapter)
        s.mount("http://", adapter)
        return s

    def _normalize_base_url(self, base: str | None) -> str:
        base = (base or "").strip()
        if base.startswith("https//"):
            base = "https://" + base[len("https//"):]
        if base.startswith("http//"):
            base = "http://" + base[len("http//"):]
        if not base.startswith(("http://", "https://")):
            scheme = getattr(settings, "DEFAULT_HTTP_SCHEME", "https")
            base = f"{scheme}://{base or 'localhost:8000'}"
        return base.rstrip("/")

    def generate_verification_link(self, info, domain: str | None = None) -> str:
        user = info.user
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        path = reverse("verify_email", kwargs={"uidb64": uid, "token": token})
        base = domain or getattr(settings, "BASE_URL", "")
        base = self._normalize_base_url(base)
        link = urljoin(base + "/", path.lstrip("/"))
        self.logger.info("email.verify.base=%s", base)
        self.logger.info("email.verify.link=%s", link)
        return link

    def send_verification(self, info) -> dict:
        user = info.user
        verify_link = self.generate_verification_link(info)
        subject = _("Email verification")
        text = _("Hello, {username}! Confirm your email by the link: {link}").format(
            username=user.username, link=verify_link
        )
        html = render_to_string("emails/verify_email.html", {"user": user, "verify_link": verify_link})
        payload = {"to": user.email, "subject": subject, "text": text, "html": html}
        return self.send_email(payload)

    def send_email(self, payload: dict) -> dict:
        method_name = self.PROVIDERS.get(self.provider)
        if not method_name:
            raise ValueError("Unsupported email provider")
        method = getattr(self, method_name)
        return method(payload)

    def _send_via_mailgun(self, payload: dict) -> dict:
        data = {
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [payload["to"]],
            "subject": payload["subject"],
            "text": payload["text"],
        }
        if "html" in payload:
            data["html"] = payload["html"]

        t0 = time.perf_counter()
        resp = self.session.post(
            settings.MAILGUN_URL,
            auth=("api", settings.MAILGUN_API_TOKEN),
            data=data,
            timeout=(3.0, 10.0),
        )
        elapsed = time.perf_counter() - t0

        ok = 200 <= resp.status_code < 300
        if not ok:
            self.logger.error(
                "mailgun_failed to=%s status=%s body=%s elapsed=%.3fs",
                payload["to"], resp.status_code, resp.text, elapsed
            )
            raise requests.exceptions.RequestException(f"Mailgun error {resp.status_code}: {resp.text}")

        try:
            body = resp.json()
        except Exception:
            body = {"message": resp.text}

        self.logger.info(
            "mailgun_ok to=%s elapsed=%.3fs message=%s",
            payload["to"], elapsed, body.get("message")
        )
        return {"status": "queued", "elapsed": elapsed, "provider": "mailgun", "response": body}
