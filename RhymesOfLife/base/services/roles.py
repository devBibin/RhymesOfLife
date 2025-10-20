from django.contrib.auth.models import Group

VALID_ROLES = {"doctor", "volunteer", "user"}


def set_user_role(user, role: str):
    if role not in VALID_ROLES:
        raise ValueError("Invalid role")
    groups = Group.objects.filter(name__in=VALID_ROLES)
    user.groups.remove(*groups)
    user.groups.add(Group.objects.get(name=role))
