import time
import signal
from orm_connector import settings
from base.notifications import ReportNotificator
from base.utils import generate_verification_link
from base.models import User
import traceback


def shutdown_handler(signum, frame):
    print("🛑 Received shutdown signal")
    exit(0)

def process_verifications():
    users = User.objects.filter(
        additional_info__ready_for_verification=True,
        additional_info__is_verified=False
    ).select_related('additional_info')

    for user in users:
        try:
            verify_link = generate_verification_link(user, domain=settings.DOMAIN)
            ReportNotificator.send_verification(user, verify_link)
            
            user.additional_info.ready_for_verification = False
            user.additional_info.save()
            
            print(f"✅ Sent verification to: {user.email}")
        except Exception as e:
            print(f"❌ Ошибка для {user.email}: {str(e)}")
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