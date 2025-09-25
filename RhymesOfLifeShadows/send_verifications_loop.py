import time
import signal
import traceback
from django.conf import settings as dj_settings
from django.utils import timezone
from RhymesOfLifeShadows.EmailVerificationSender import EmailVerificationSender
from base.models import AdditionalUserInfo
from RhymesOfLifeShadows.create_log import create_log

log = create_log("verification.log", "EmailSender")


def shutdown_handler(signum, frame):
    log.info("received_shutdown_signal")
    raise SystemExit(0)


def process_verifications(batch_size: int = 100):
    sender = EmailVerificationSender(provider="mailgun", logger=log)
    qs = AdditionalUserInfo.objects.filter(
        ready_for_verification=True,
        is_verified=False
    ).select_related("user")[:batch_size]

    now = timezone.now()
    for info in qs:
        try:
            res = sender.send_verification(info)
            info.ready_for_verification = False
            info.save(update_fields=["ready_for_verification"])
            log.info(
                "sent user_id=%s email=%s elapsed=%.3f",
                info.user_id,
                info.email or info.user.email,
                float(res.get("elapsed") or -1.0),
            )
        except Exception as e:
            log.error("send_error user_id=%s email=%s err=%s", info.user_id, info.email or info.user.email, str(e))
            log.debug(traceback.format_exc())


def main():
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    log.info("worker_start")
    while True:
        try:
            process_verifications()
        except SystemExit:
            break
        except Exception as e:
            log.critical("critical_error err=%s", str(e))
        time.sleep(2)


if __name__ == "__main__":
    main()
