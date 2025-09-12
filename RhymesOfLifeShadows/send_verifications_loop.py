import time
import signal
import traceback

from orm_connector import settings
from RhymesOfLifeShadows.EmailVerificationSender import EmailVerificationSender
from base.models import AdditionalUserInfo
from RhymesOfLifeShadows.create_log import create_log

log = create_log("verification.log", "EmailSender")


def shutdown_handler(signum, frame):
    log.info("🛑 Received shutdown signal")
    exit(0)


def process_verifications():
    sender = EmailVerificationSender(provider='mailgun', logger=log)

    verifications = AdditionalUserInfo.objects.filter(
        ready_for_verification=True,
        is_verified=False
    )

    for info in verifications:
        try:
            sender.send_verification(info)
            info.ready_for_verification = False
            info.save()
            log.info(f"✅ Sent verification to: {info.email or info.user.email}")
        except Exception as e:
            log.error(f"❌ Error for {info.email or info.user.email}: {str(e)}")
            log.exception(e)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    log.info("🔁 Starting verification worker")
    while True:
        try:
            process_verifications()
            time.sleep(10)
        except Exception as e:
            log.critical(f"⚠️ Critical error: {str(e)}")
            time.sleep(60)
