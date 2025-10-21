from django import template

register = template.Library()


@register.filter(name="hasperm")
def hasperm(user, codename: str) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    return user.has_perm(codename)


@register.filter(name="ingroup")
def ingroup(user, group_names: str) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    names = {g.name for g in user.groups.all()}
    wanted = {g.strip() for g in (group_names or "").split(",") if g.strip()}
    return bool(names.intersection(wanted))


@register.filter(name="hasanyperm")
def hasanyperm(user, codenames: str) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    codes = [c.strip() for c in (codenames or "").split(",") if c.strip()]
    return any(user.has_perm(c) for c in codes)
