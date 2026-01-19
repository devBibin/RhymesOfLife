import time
import signal
import traceback

from orm_connector import settings
from RhymesOfLifeShadows.EmailVerificationSender import EmailVerificationSender
from base.models import AdditionalUserInfo
from RhymesOfLifeShadows.create_log import create_log

log = create_log("verification.log", "EmailSender")


def shutdown_handler(signum, frame):
    log.info("worker.shutdown.signal=%s", signum)
    exit(0)


def process_verifications():
    sender = EmailVerificationSender(provider="postbox_api", logger=log)

    verifications = AdditionalUserInfo.objects.filter(
        ready_for_verification=True,
        is_verified=False,
    )

    for info in verifications:
        email = info.email or info.user.email
        try:
            sender.send_verification(info)
            info.ready_for_verification = False
            info.save(update_fields=["ready_for_verification"])
            log.info("verification.sent email=%s", email)
        except Exception as e:
            log.error("verification.failed email=%s error=%s", email, str(e))
            log.exception(e)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    log.info("worker.started verification")

    while True:
        try:
            process_verifications()
            time.sleep(5)
        except Exception as e:
            log.critical("worker.crash error=%s", str(e))
            time.sleep(30)
