from RhymesOfLifeShadows.EmailVerificationSender import EmailVerificationSender


def send_email(payload: dict, *, logger=None) -> bool:
    sender = EmailVerificationSender(provider="postbox_api", logger=logger)
    return bool(sender.send_email(payload))
