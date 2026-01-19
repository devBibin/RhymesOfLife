from urllib.parse import urljoin

from django.conf import settings
import boto3
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
        return urljoin(base + "/", path.lstrip("/"))

    def send_verification(self, info):
        user = info.user
        self.logger.info("email.verify.prepare user_id=%s email=%s", user.id, user.email)
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
            payload.get("subject"),
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
            payload["subject"],
            payload["text"],
            from_email,
            [payload["to"]],
        )

        if payload.get("html"):
            msg.attach_alternative(payload["html"], "text/html")

        msg.send(fail_silently=False)
        self.logger.info("email.sent.smtp to=%s", payload["to"])
        return True

    def _postbox_client(self):
        return boto3.client(
            "sesv2",
            region_name=settings.POSTBOX_REGION,
            endpoint_url=settings.POSTBOX_ENDPOINT,
            aws_access_key_id=settings.POSTBOX_ACCESS_KEY_ID,
            aws_secret_access_key=settings.POSTBOX_SECRET_ACCESS_KEY,
        )

    def _send_via_postbox_api(self, payload: dict):
        client = self._postbox_client()

        from_email = (
            payload.get("from_email")
            or getattr(settings, "POSTBOX_FROM_EMAIL", None)
            or getattr(settings, "DEFAULT_FROM_EMAIL", None)
        )

        if not from_email:
            raise ValueError("POSTBOX_FROM_EMAIL is not configured")

        body = {}
        if payload.get("text"):
            body["Text"] = {"Data": payload["text"], "Charset": "UTF-8"}
        if payload.get("html"):
            body["Html"] = {"Data": payload["html"], "Charset": "UTF-8"}

        response = client.send_email(
            FromEmailAddress=from_email,
            Destination={"ToAddresses": [payload["to"]]},
            Content={
                "Simple": {
                    "Subject": {
                        "Data": payload["subject"],
                        "Charset": "UTF-8",
                    },
                    "Body": body,
                }
            },
        )

        self.logger.info(
            "email.sent.postbox_api to=%s message_id=%s",
            payload["to"],
            response.get("MessageId"),
        )
        return True
