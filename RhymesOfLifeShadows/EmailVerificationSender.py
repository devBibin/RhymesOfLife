from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
import requests
from django.conf import settings



class EmailVerificationSender:


    # Registry of available email providers mapped to their send methods
    PROVIDERS = {
        'mailgun': '_send_via_mailgun',
        # Add new providers here in format: 'provider_name': '_send_method_name'
    }

    #Generates a unique email verification link for the user
    @staticmethod
    def generate_verification_link(info, domain=None):
        
        user = info.user
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        if not domain:
            domain = getattr(settings, "BASE_URL", "localhost:8000")

        url = reverse('verify_email', kwargs={'uidb64': uid, 'token': token})
        return f"http://{domain}{url}"

    #Main email handler that routes sending to the appropriate provider
    @staticmethod
    def send_email(subject, to_email, text, html=None, provider='mailgun'):

        send_method_name = EmailVerificationSender.PROVIDERS.get(provider)
        if not send_method_name:
            raise ValueError(f"Unsupported email provider: {provider}")
        
        send_method = getattr(EmailVerificationSender, send_method_name)
        return send_method(subject, to_email, text, html)
    
    #Private method to handle email sending via Mailgun API
    @staticmethod
    def _send_via_mailgun(subject, to_email, text, html=None):
 
        data = {
            "from": settings.DEFAULT_FROM_EMAIL,
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

        # Make API request to Mailgun
        requests.post(
            settings.MAILGUN_URL,
            auth=("api", settings.MAILGUN_API_TOKEN),
            data=data,
        )

    # Sends email verification message to the user
    @staticmethod
    def send_verification(user, verify_link, provider='mailgun'):
        subject = "Подтверждение email"
        text = f"Привет, {user.username}! Подтверди свой email по ссылке: {verify_link}"
        html = render_to_string("emails/verify_email.html", {
            "user": user,
            "verify_link": verify_link,
        })
        return EmailVerificationSender.send_email(
            subject, 
            user.email, 
            text, 
            html,
            provider=provider
        )