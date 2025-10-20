import os
import time
import signal
from datetime import date, timedelta

from orm_connector import settings  # noqa: F401

from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import override
from django.db.models import Max, Q
from django.db.models.functions import TruncDate

from RhymesOfLifeShadows.create_log import create_log
from base.models import AdditionalUserInfo, Notification
from base.utils.notify import send_notification_multichannel

try:
    import redis  # type: ignore
except Exception:
    redis = None

log = create_log("wellness_reminders.log", "WellnessReminders")


def get_redis():
    if not redis:
        return None
    host = os.getenv("REDIS_HOST", "redis")
    port = int(os.getenv("REDIS_PORT", "6379"))
    try:
        return redis.Redis(host=host, port=port, decode_responses=True)
    except Exception:
        return None


def shutdown_handler(signum, frame):
    log.info("shutdown")
    raise SystemExit


def already_sent(redis_cli, user_id: int, today: date) -> bool:
    if not redis_cli:
        return False
    key = f"wellness:reminded:{user_id}:{today.isoformat()}"
    try:
        ok = redis_cli.set(key, "1", nx=True, ex=60 * 60 * 26)
        return ok is None
    except Exception:
        return False


def already_sent_db(info: AdditionalUserInfo, today: date) -> bool:
    return Notification.objects.filter(
        recipient=info,
        notification_type="SYSTEM_MESSAGE",
        payload__kind="wellness_reminder",
    ).annotate(d=TruncDate("created_at")).filter(d=today).exists()


def mark_sent_db(info: AdditionalUserInfo, title: str, message: str) -> None:
    Notification.objects.create(
        recipient=info,
        sender=None,
        notification_type="SYSTEM_MESSAGE",
        title=title,
        message=message,
        url="",
        payload={"kind": "wellness_reminder"},
        source=Notification.Source.SYSTEM,
        scope=Notification.Scope.PERSONAL,
    )


def due_now(now_local, hh: int, mm: int) -> bool:
    due_dt = now_local.replace(hour=hh, minute=mm, second=0, microsecond=0)
    return now_local >= due_dt


def build_message(info: AdditionalUserInfo) -> str:
    with override(info.language or "en"):
        return _("You haven't checked in for a while. Please rate your wellness (1–10) and leave a short note.")


def loop_once() -> int:
    tz = timezone.get_current_timezone()
    now_local = timezone.now().astimezone(tz)
    today = now_local.date()

    qs = (
        AdditionalUserInfo.objects
        .select_related("user", "telegram_account", "wellness_settings")
        .annotate(last_entry=Max("wellness_entries__date"))
        .filter(
            wellness_settings__isnull=False,
            wellness_settings__tg_notifications_enabled=True,
            telegram_account__telegram_verified=True,
            telegram_account__telegram_id__isnull=False,
        )
    )

    sent = 0
    rds = get_redis()

    for info in qs:
        s = info.wellness_settings
        interval_days = getattr(s, "reminder_interval", 3) or 3
        if interval_days == 0:
            continue

        threshold = today - timedelta(days=interval_days)
        if info.last_entry and info.last_entry > threshold:
            continue

        if not due_now(now_local, s.reminder_hour, s.reminder_minute):
            continue
        if rds and already_sent(rds, info.pk, today):
            continue
        if already_sent_db(info, today):
            continue

        with override(info.language or "en"):
            title = _("Wellness reminder")
            msg = build_message(info)

        res = send_notification_multichannel(
            recipient=info,
            sender=None,
            notification_type="SYSTEM_MESSAGE",
            title=title,
            message=msg,
            url="",
            payload={"kind": "wellness_reminder"},
            source=Notification.Source.SYSTEM,
            scope=Notification.Scope.PERSONAL,
            via_site=True,
            via_telegram=True,
            via_email=False,
            email_subject=None,
            email_body=None,
        )

        if res.get("telegram_sent") or res.get("notification_id"):
            sent += 1
            log.info(f"sent to user_info={info.pk}")
        else:
            mark_sent_db(info, str(title), str(msg))
            log.warning(f"telegram failed; marked in DB user_info={info.pk}")

    return sent


def main():
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    log.info("start wellness reminders")
    while True:
        try:
            loop_once()
            time.sleep(60)
        except SystemExit:
            break
        except Exception as e:
            log.exception(e)
            time.sleep(30)


if __name__ == "__main__":
    main()
