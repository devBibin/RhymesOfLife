from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from ..utils.logging import get_app_logger

log = get_app_logger(__name__)


def staff_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            messages.error(request, _("You don't have permission to view this page."))
            log.warning("Staff-required rejected: user_id=%s path=%s", getattr(request.user, "id", None), request.path)
            return redirect("home")
        return view_func(request, *args, **kwargs)
    return _wrapped


def permission_or_staff_required(*perms, redirect_name="home"):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            u = request.user
            if not u.is_authenticated:
                messages.error(request, _("You don't have permission to view this page."))
                return redirect(redirect_name)
            if u.is_superuser or u.is_staff or u.has_perms(perms):
                return view_func(request, *args, **kwargs)
            messages.error(request, _("You don't have permission to view this page."))
            return redirect(redirect_name)
        return _wrapped
    return decorator
