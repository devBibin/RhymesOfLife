from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _


@login_required
@require_GET
def banned_view(request):
    info = getattr(request.user, "additional_info", None)
    ctx = {
        "reason": getattr(info, "banned_reason", "") or "",
        "at": getattr(info, "banned_at", None),
    }
    return render(request, "base/banned.html", ctx)
