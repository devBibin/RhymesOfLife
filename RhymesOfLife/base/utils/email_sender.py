from pathlib import Path
import sys

try:
    from RhymesOfLifeShadows.EmailVerificationSender import EmailVerificationSender
except ModuleNotFoundError:
    # Ensure project root is on sys.path when manage.py lives in a subdir.
    root = Path(__file__).resolve().parents[3]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from RhymesOfLifeShadows.EmailVerificationSender import EmailVerificationSender


def send_email(payload: dict, *, logger=None) -> bool:
    sender = EmailVerificationSender(provider="postbox_api", logger=logger)
    return bool(sender.send_email(payload))
