from base.utils import MailgunClient
from django.template.loader import render_to_string


class ReportNotificator:
    @staticmethod
    def send_verification(user, verify_link):
        subject = "Подтверждение email"
        text = f"Привет, {user.username}! Подтверди свой email по ссылке: {verify_link}"
        html = render_to_string("emails/verify_email.html", {
            "user": user,
            "verify_link": verify_link,
        })
        return MailgunClient.send_email(subject, user.email, text, html)
