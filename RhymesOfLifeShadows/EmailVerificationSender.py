from urllib.parse import urljoin

import requests
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.conf import settings
from django.utils.translation import gettext as _


class EmailVerificationSender:
    PROVIDERS = {
        "mailgun": "_send_via_mailgun",
    }

    def __init__(self, provider: str = "mailgun", logger=None):
        self.provider = provider
        self.logger = logger or self._default_logger()

    def _default_logger(self):
        import logging
        return logging.getLogger(__name__)

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

    def send_verification(self, info):
        user = info.user
        verify_link = self.generate_verification_link(info)
        subject = _("Email verification")
        text = _("Hello, {username}! Confirm your email by the link: {link}").format(
            username=user.username,
            link=verify_link,
        )
        html = render_to_string(
            "emails/verify_email.html",
            {"user": user, "verify_link": verify_link},
        )
        payload = {"to": user.email, "subject": subject, "text": text, "html": html}
        return self.send_email(payload)

    def send_email(self, payload: dict):
        method_name = self.PROVIDERS.get(self.provider)
        if not method_name:
            raise ValueError("Unsupported email provider")
        method = getattr(self, method_name)
        return method(payload)

    def _send_via_mailgun(self, payload: dict):
        data = {
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [payload["to"]],
            "subject": payload["subject"],
            "text": payload["text"],
        }
        if "html" in payload:
            data["html"] = payload["html"]
        response = requests.post(
            settings.MAILGUN_URL,
            auth=("api", settings.MAILGUN_API_TOKEN),
            data=data,
            timeout=20,
        )
        if response.status_code != 200:
            self.logger.error(
                "Mailgun failed for %s: %s - %s",
                payload["to"],
                response.status_code,
                response.text,
            )
            raise requests.exceptions.RequestException(
                f"Mailgun error {response.status_code}: {response.text}"
            )
        self.logger.info("Verification sent to: %s", payload["to"])
        return True
