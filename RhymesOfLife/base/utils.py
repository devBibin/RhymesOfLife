from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
import requests
from django.conf import settings


# Utility function to generate a verification link for email confirmation
def generate_verification_link(user, request=None, domain=None):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    if request and not domain:
        from django.contrib.sites.shortcuts import get_current_site
        domain = get_current_site(request).domain

    if not domain:
        domain = "localhost:8000"  # или example.com

    url = reverse('verify_email', kwargs={'uidb64': uid, 'token': token})
    return f"http://{domain}{url}"



# Mailgun client for sending emails
class MailgunClient:
    @staticmethod
    def send_email(subject, to_email, text, html=None):
        data = {
            "from": "Rhymes of Life <admin@igstan.com>",
            "to": [to_email],
            "subject": subject,
            "text": text,
        }

        if html:
            data["html"] = html

        print(f"📤 Mailgun request to: {settings.MAILGUN_URL}")
        print(f"📤 Sending to: {to_email}")
        print(f"📤 Subject: {subject}")
        print(f"📤 Token exists: {'✅' if settings.MAILGUN_API_TOKEN else '❌ NO TOKEN'}")

        response = requests.post(
            settings.MAILGUN_URL,
            auth=("api", settings.MAILGUN_API_TOKEN),
            data=data,
        )

        print(f"📬 Mailgun response: {response.status_code} - {response.text}")

        if response.status_code != 200:
            raise Exception(f"Mailgun error {response.status_code}: {response.text}")
        return response
