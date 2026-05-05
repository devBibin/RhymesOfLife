from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ...utils.telegram import send_bot_message


class Command(BaseCommand):
    help = "Send a test Telegram message using the configured proxy-aware client."

    def add_arguments(self, parser):
        parser.add_argument("--chat-id", required=True, help="Target Telegram chat id.")
        parser.add_argument(
            "--bot",
            choices=("users", "admin"),
            default="users",
            help="Which configured bot token to use.",
        )
        parser.add_argument(
            "--text",
            default="Telegram proxy test from RhymesOfLife",
            help="Message text.",
        )

    def handle(self, *args, **options):
        token = (
            settings.TELEGRAM_BOT_TOKEN_USERS
            if options["bot"] == "users"
            else settings.TELEGRAM_BOT_TOKEN_ADMIN
        )
        if not token:
            raise CommandError(f"TELEGRAM_BOT_TOKEN_{options['bot'].upper()} is not configured")

        ok = send_bot_message(
            token=token,
            chat_id=options["chat_id"],
            text=options["text"],
        )
        if not ok:
            raise CommandError("Telegram test message failed. Check application logs for details.")

        self.stdout.write(self.style.SUCCESS("Telegram test message sent successfully."))
