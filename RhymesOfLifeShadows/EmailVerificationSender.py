import requests
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.conf import settings


class EmailVerificationSender:
    """
    Handler class for sending email verifications via pluggable providers.
    Usage:
        sender = EmailVerificationSender(provider='mailgun')
        sender.send_verification(info)
    """
    PROVIDERS = {
        'mailgun': '_send_via_mailgun',
        # 'smtp': '_send_via_smtp',  # Example for future
    }

    def __init__(self, provider='mailgun'):
        self.provider = provider

    def generate_verification_link(self, info, domain=None):
        user = info.user
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        domain = domain or getattr(settings, "BASE_URL", "localhost:8000")
        url = reverse('verify_email', kwargs={'uidb64': uid, 'token': token})
        return f"http://{domain}{url}"

    def send_verification(self, info):
        user = info.user
        verify_link = self.generate_verification_link(info)

        payload = {
            "to": user.email,
            "subject": "Подтверждение email",
            "text": f"Привет, {user.username}! Подтверди свой email по ссылке: {verify_link}",
            "html": render_to_string("emails/verify_email.html", {
                "user": user,
                "verify_link": verify_link,
            })
        }

        return self.send_email(payload)

    def send_email(self, payload: dict):
        method_name = self.PROVIDERS.get(self.provider)
        if not method_name:
            raise ValueError(f"Unsupported email provider: {self.provider}")

        method = getattr(self, method_name)
        return method(payload)

    def _send_via_mailgun(self, payload: dict):
        data = {
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [payload['to']],
            "subject": payload['subject'],
            "text": payload['text'],
        }

        if 'html' in payload:
            data['html'] = payload['html']

        print(f"📤 Mailgun request to: {settings.MAILGUN_URL}")
        print(f"📤 Sending to: {payload['to']}")
        print(f"📤 Subject: {payload['subject']}")
        print(f"📤 Token exists: {'✅' if settings.MAILGUN_API_TOKEN else '❌ NO TOKEN'}")

        response = requests.post(
            settings.MAILGUN_URL,
            auth=("api", settings.MAILGUN_API_TOKEN),
            data=data,
        )

        print(f"📬 Mailgun response: {response.status_code} - {response.text}")

        if response.status_code != 200:
            raise requests.exceptions.RequestException(
                f"Mailgun error {response.status_code}: {response.text}"
            )
        return response
