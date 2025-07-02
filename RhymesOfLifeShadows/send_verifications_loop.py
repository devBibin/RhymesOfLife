import time
import signal
import traceback

from orm_connector import settings
from RhymesOfLifeShadows.EmailVerificationSender import EmailVerificationSender
from base.models import AdditionalUserInfo


def shutdown_handler(signum, frame):
    print("🛑 Received shutdown signal")
    exit(0)

def process_verifications():
    verifications = AdditionalUserInfo.objects.filter(
        ready_for_verification=True,
        is_verified=False
    )

    for info in verifications:
        try:
            verify_link = EmailVerificationSender.generate_verification_link(info, domain=settings.BASE_URL)
            EmailVerificationSender.send_verification(info.user, verify_link)

            info.ready_for_verification = False
            info.save()

            print(f"✅ Sent verification to: {info.email or info.user.email}")
        except Exception as e:
            print(f"❌ Error for {info.email or info.user.email}: {str(e)}")
            traceback.print_exc()
if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    print("🔁 Starting verification worker")
    while True:
        try:
            process_verifications()
            time.sleep(10)
        except Exception as e:
            print(f"⚠️ Critical error: {str(e)}")
            time.sleep(60)