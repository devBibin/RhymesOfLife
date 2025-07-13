def can_write(article, user):
    return hasattr(user, 'is_superuser') and (
        user.is_superuser or article.current_revision.user == user
    )

def can_delete(article, user):
    return hasattr(user, 'is_superuser') and (
        user.is_superuser or article.current_revision.user == user
    )

def can_moderate(article, user):
    return hasattr(user, 'is_superuser') and user.is_superuser
