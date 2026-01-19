from __future__ import annotations

from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext as _


class EmailVerificationSender:
    PROVIDERS = {
        "smtp": "_send_via_smtp",
        "postbox_api": "_send_via_postbox_api",
    }

    def __init__(self, provider: str = "postbox_api", logger=None):
        self.provider = (provider or "postbox_api").strip().lower()
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
        return urljoin(base + "/", path.lstrip("/"))

    def send_verification(self, info):
        user = info.user
        self.logger.info("email.verify.prepare user_id=%s email=%s", user.id, getattr(user, "email", None))
        verify_link = self.generate_verification_link(info)

        subject = _("Email verification")
        text = _("Hello, {username}! Confirm your email by the link: {link}").format(
            username=user.username,
            link=verify_link,
        )
        html = render_to_string("emails/verify_email.html", {"user": user, "verify_link": verify_link})

        payload = {
            "to": user.email,
            "subject": subject,
            "text": text,
            "html": html,
        }
        return self.send_email(payload)

    def send_email(self, payload: dict):
        method_name = self.PROVIDERS.get(self.provider)
        if not method_name:
            raise ValueError("Unsupported email provider")

        self.logger.info(
            "email.send provider=%s to=%s subject=%s",
            self.provider,
            payload.get("to"),
            str(payload.get("subject"))[:160] if payload.get("subject") is not None else "",
        )
        return getattr(self, method_name)(payload)

    def _send_via_smtp(self, payload: dict):
        from django.core.mail import EmailMultiAlternatives

        from_email = (
            payload.get("from_email")
            or getattr(settings, "DEFAULT_FROM_EMAIL", None)
            or getattr(settings, "EMAIL_HOST_USER", None)
        )

        msg = EmailMultiAlternatives(
            str(payload.get("subject") or ""),
            str(payload.get("text") or ""),
            from_email,
            [str(payload.get("to") or "")],
        )

        if payload.get("html"):
            msg.attach_alternative(str(payload["html"]), "text/html")

        msg.send(fail_silently=False)
        self.logger.info("email.sent.smtp to=%s", payload.get("to"))
        return True

    def _postbox_client(self):
        try:
            import boto3
            from botocore.config import Config
        except ModuleNotFoundError as exc:
            raise RuntimeError("boto3 is required for postbox_api provider") from exc
        access_key = getattr(settings, "POSTBOX_ACCESS_KEY_ID", None)
        secret_key = getattr(settings, "POSTBOX_SECRET_ACCESS_KEY", None)
        region = getattr(settings, "POSTBOX_REGION", None) or "ru-central1"
        endpoint = getattr(settings, "POSTBOX_ENDPOINT", None) or "https://postbox.cloud.yandex.net"

        has_access = bool(access_key)
        has_secret = bool(secret_key)

        self.logger.info(
            "postbox.client.config region=%s endpoint=%s has_access_key=%s has_secret_key=%s",
            region,
            endpoint,
            has_access,
            has_secret,
        )

        if not has_access or not has_secret:
            raise RuntimeError("Postbox credentials are missing in settings (POSTBOX_ACCESS_KEY_ID/POSTBOX_SECRET_ACCESS_KEY)")

        cfg = Config(
            region_name=region,
            retries={"max_attempts": 5, "mode": "standard"},
            connect_timeout=10,
            read_timeout=20,
        )

        return boto3.client(
            "sesv2",
            region_name=region,
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=cfg,
        )

    def _send_via_postbox_api(self, payload: dict):
        client = self._postbox_client()

        from_email = (
            payload.get("from_email")
            or getattr(settings, "POSTBOX_FROM_EMAIL", None)
            or getattr(settings, "DEFAULT_FROM_EMAIL", None)
        )
        if not from_email:
            raise RuntimeError("POSTBOX_FROM_EMAIL is not configured (and no from_email provided)")

        to_addr = str(payload.get("to") or "").strip()
        subject = str(payload.get("subject") or "").strip()
        text = str(payload.get("text") or "")
        html = payload.get("html")
        html = str(html) if html is not None else None

        body = {}
        if text.strip():
            body["Text"] = {"Data": text, "Charset": "UTF-8"}
        if html and html.strip():
            body["Html"] = {"Data": html, "Charset": "UTF-8"}

        self.logger.info(
            "postbox.send.prepare to=%s from=%s subject=%s",
            to_addr,
            str(from_email),
            subject[:160],
        )

        response = client.send_email(
            FromEmailAddress=str(from_email),
            Destination={"ToAddresses": [to_addr]},
            Content={
                "Simple": {
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": body,
                }
            },
        )

        msg_id = response.get("MessageId") if isinstance(response, dict) else None
        req_id = None
        try:
            req_id = response.get("ResponseMetadata", {}).get("RequestId")
        except Exception:
            req_id = None

        self.logger.info("postbox.send.ok to=%s message_id=%s request_id=%s", to_addr, msg_id or "-", req_id or "-")
        return True
