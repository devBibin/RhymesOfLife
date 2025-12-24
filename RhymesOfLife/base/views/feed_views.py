from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods, require_POST
from django.utils.timezone import localtime
from django.views.decorators.csrf import csrf_protect

from base.models import AdditionalUserInfo
from base.models import Post, PostImage, PostLike, PostComment, PostReport
from base.utils.files import validate_mixed_upload
from base.utils.moderation import get_moderation_config
from base.utils.decorators import permission_or_staff_required

ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_SIDE_PX = 10_000
MAX_IMAGES_PER_POST = 10
FIRST_COMMENTS_LIMIT = 3
AUTO_CENSOR_REPORTS = 15


def _validate_images(files):
    errors = []
    if len(files) > MAX_IMAGES_PER_POST:
        errors.append(_("Too many images."))
        return errors
    for f in files:
        ok, err = validate_mixed_upload(
            f,
            allowed_exts=ALLOWED_IMAGE_EXTS,
            allowed_mimes=ALLOWED_IMAGE_MIMES,
            max_size_bytes=MAX_FILE_SIZE_BYTES,
            max_image_side_px=MAX_IMAGE_SIDE_PX,
        )
        if not ok:
            errors.append(_("%(msg)s") % {"msg": err})
    return errors


def _report_threshold():
    _, threshold = get_moderation_config()
    return threshold


def _me(request):
    return AdditionalUserInfo.objects.filter(user=request.user).first() if request.user.is_authenticated else None


def _can_view_pending(user):
    return user.is_staff or user.has_perm("base.view_pending_posts")


def _can_moderate(user):
    return user.is_staff or user.has_perm("base.moderate_posts")


def _feed_queryset(request):
    f = request.GET.get("filter", "mine" if request.user.is_authenticated else "latest")

    base = Post.objects.filter(is_deleted=False)
    public_base = base.filter(is_hidden=False, is_hidden_by_reports=False, is_approved=True)

    if f == "mine" and request.user.is_authenticated:
        me = _me(request)
        qs = base.filter(author=me).order_by("-created_at")
    elif f == "subscriptions" and request.user.is_authenticated:
        me = _me(request)
        follow_ids = me.following.filter(is_active=True).values_list("following_id", flat=True)
        qs = public_base.filter(author__in=follow_ids).order_by("-created_at")
    elif f == "pending" and _can_view_pending(request.user):
        qs = base.filter(is_approved=False, is_hidden_by_reports=False).order_by("-created_at")
    else:
        f = "latest"
        qs = public_base.order_by("-created_at")

    return f, qs


def _render_post_list_fragment(request, context):
    html = render_to_string("base/post_list_fragment.html", context, request=request)
    return html


def _render_single_post_card(request, post, liked_ids=None, following_user_ids=None, current_filter="latest"):
    ctx = {
        "posts": [post],
        "liked_ids": liked_ids or [],
        "following_user_ids": list(following_user_ids or []),
        "current_filter": current_filter,
        "FIRST_COMMENTS_LIMIT": FIRST_COMMENTS_LIMIT,
        "report_threshold": _report_threshold(),
    }
    return render_to_string("base/post_cards.html", ctx, request=request)


@login_required
def feed(request):
    if not request.user.is_authenticated:
        return render(request, "base/info/main.html")

    f, qs = _feed_queryset(request)
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    liked_ids = []
    following_user_ids = set()

    me = _me(request)
    if me:
        liked_ids = list(
            PostLike.objects.filter(author=me, is_active=True, post__in=page_obj.object_list)
            .values_list("post_id", flat=True)
        )
        following_user_ids = set(me.following.filter(is_active=True).values_list("following__user_id", flat=True))

    threshold = _report_threshold()

    if me:
        my_base = Post.objects.filter(
            author=me, is_deleted=False, is_hidden=False, is_hidden_by_reports=False
        )
        posts_total = my_base.filter(is_approved=True).count()
    else:
        posts_total = 0

    context = {
        "posts": page_obj,
        "current_filter": f,
        "liked_ids": liked_ids,
        "following_user_ids": list(following_user_ids),
        "FIRST_COMMENTS_LIMIT": FIRST_COMMENTS_LIMIT,
        "info": me,
        "profile_user": request.user,
        "posts_total": posts_total,
        "report_threshold": threshold,
    }

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = _render_post_list_fragment(request, context)
        return JsonResponse({"html": html})

    return render(request, "base/feed.html", context)


@login_required
@require_http_methods(["GET", "POST"])
@csrf_protect
@transaction.atomic
def create_post(request):
    if request.method != "POST":
        # supports ajax modal/form fetch if needed later
        return render(request, "base/post_create.html")

    me = AdditionalUserInfo.objects.get(user=request.user)
    text = (request.POST.get("text") or "").strip()
    files = request.FILES.getlist("images")

    errors = _validate_images(files)
    if not text and not files:
        errors.append(_("Post must contain text or an image."))

    if errors:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "errors": errors}, status=400)
        return render(request, "base/post_create.html", {"errors": errors, "text": text})

    auto = _can_moderate(request.user) or not me.censorship_enabled

    post = Post.objects.create(
        author=me,
        text=text,
        is_approved=auto,
        approved_at=timezone.now() if auto else None,
        approved_by=request.user if auto else None,
    )
    for f in files:
        PostImage.objects.create(post=post, image=f)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        liked_ids = []
        following_user_ids = set(me.following.filter(is_active=True).values_list("following__user_id", flat=True))
        card_html = _render_single_post_card(
            request, post, liked_ids=liked_ids, following_user_ids=following_user_ids, current_filter="mine"
        )
        msg = _("Your post is under review. It will appear after approval.") if not auto else _("Post published.")
        return JsonResponse({
            "ok": True,
            "approved": bool(auto),
            "html": card_html,
            "message": msg,
            "redirect": reverse("home"),
        })

    return redirect("home")


@login_required
@require_http_methods(["GET", "POST"])
@csrf_protect
@transaction.atomic
def edit_post(request, post_id: int):
    post = get_object_or_404(Post, pk=post_id, is_deleted=False)
    me = _me(request)
    if not me or (post.author_id != me.id and not request.user.is_superuser):
        return HttpResponseForbidden()

    if request.method == "POST":
        text = (request.POST.get("text") or "").strip()
        files = request.FILES.getlist("images")
        remove_ids = request.POST.getlist("remove")
        errors = _validate_images(files)
        if errors:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"ok": False, "errors": errors}, status=400)
            return render(request, "base/post_edit.html", {"post": post, "errors": errors, "text": text})

        post.text = text
        post.save(update_fields=["text"])

        if remove_ids:
            ids = [int(i) for i in remove_ids if str(i).isdigit()]
            qs = PostImage.objects.filter(post=post, pk__in=ids)
            has_soft = any(f.name == "is_deleted" for f in qs.model._meta.fields)
            if has_soft:
                qs.update(is_deleted=True)
            else:
                qs.delete()

        for f in files:
            PostImage.objects.create(post=post, image=f)

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            liked_ids = list(
                PostLike.objects.filter(post=post, is_active=True, author=me).values_list("post_id", flat=True)
            )
            following_user_ids = set(me.following.filter(is_active=True).values_list("following__user_id", flat=True))
            html = _render_single_post_card(
                request, post, liked_ids=liked_ids, following_user_ids=following_user_ids
            )
            return JsonResponse({"ok": True, "html": html, "post_id": post.id, "message": _("Post updated.")})

        return render(request, "base/post_edit.html", {"post": post})

    return render(request, "base/post_edit.html", {"post": post})


@login_required
@require_POST
@csrf_protect
def report_post(request, post_id: int):
    post = get_object_or_404(Post, pk=post_id, is_deleted=False)
    me = AdditionalUserInfo.objects.get(user=request.user)
    if post.author_id == me.id:
        return JsonResponse({"error": _("You cannot report your own post.")}, status=400)

    threshold = _report_threshold()
    _, created = PostReport.objects.get_or_create(post=post, author=me)
    if created:
        cnt = PostReport.objects.filter(post=post).count()
        hide = cnt >= threshold
        if hide and not post.is_hidden_by_reports:
            post.is_hidden_by_reports = True
            post.reports_count = cnt
            post.save(update_fields=["is_hidden_by_reports", "reports_count"])
        else:
            post.reports_count = cnt
            post.save(update_fields=["reports_count"])

        if cnt >= AUTO_CENSOR_REPORTS and not post.author.censorship_enabled:
            info = post.author
            info.censorship_enabled = True
            info.save(update_fields=["censorship_enabled"])

    return JsonResponse({"ok": True, "reports": post.reports_count, "hidden": post.is_hidden_by_reports})


@login_required
@require_POST
def hide_post(request, post_id: int):
    post = get_object_or_404(Post, pk=post_id, is_deleted=False)
    me = _me(request)
    if not me or (post.author_id != me.id and not request.user.is_superuser):
        return HttpResponseForbidden()
    post.is_hidden = True
    post.save(update_fields=["is_hidden"])
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "post_id": post.id})
    return JsonResponse({"ok": True})


@login_required
@require_POST
def unhide_post(request, post_id: int):
    post = get_object_or_404(Post, pk=post_id, is_deleted=False)
    me = _me(request)
    if not me or (post.author_id != me.id and not request.user.is_superuser):
        return HttpResponseForbidden()
    post.is_hidden = False
    post.save(update_fields=["is_hidden"])
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        liked_ids = []
        following_user_ids = set()
        html = _render_single_post_card(request, post, liked_ids, following_user_ids)
        return JsonResponse({"ok": True, "post_id": post.id, "html": html})
    return JsonResponse({"ok": True})


@login_required
@require_POST
@csrf_protect
def toggle_like(request, post_id: int):
    post = get_object_or_404(Post, pk=post_id, is_deleted=False)
    me = AdditionalUserInfo.objects.get(user=request.user)
    like, created = PostLike.objects.get_or_create(post=post, author=me, defaults={"is_active": True})
    if not created:
        like.is_active = not like.is_active
        like.save(update_fields=["is_active"])

    post.likes_count = PostLike.objects.filter(post=post, is_active=True).count()
    post.save(update_fields=["likes_count"])

    return JsonResponse({"liked": like.is_active, "like_count": post.likes_count})


def serialize_comment(c, request):
    info = c.author
    user = info.user
    can_delete = (user == request.user) or _can_moderate(request.user)
    avatar_url = getattr(getattr(info, "avatar", None), "url", "/static/img/avatar-default.png")
    return {
        "id": c.id,
        "post": c.post_id,
        "author": {
            "username": user.username,
            "avatar": avatar_url,
        },
        "created_at": localtime(c.created_at).isoformat(),
        "can_delete": can_delete,
        "text": c.text,
    }


@login_required
@require_POST
@csrf_protect
def add_comment(request, post_id: int):
    post = get_object_or_404(Post, pk=post_id, is_deleted=False)
    me = AdditionalUserInfo.objects.get(user=request.user)
    text = (request.POST.get("text") or "").strip()
    if not text:
        return JsonResponse({"error": "empty"}, status=400)

    c = PostComment.objects.create(post=post, author=me, text=text)
    post.comments_count = PostComment.objects.filter(post=post, is_deleted=False).count()
    post.save(update_fields=["comments_count"])

    data = serialize_comment(c, request)
    return JsonResponse({"item": data, "post": post.id, "count": post.comments_count})


@login_required
@require_POST
@csrf_protect
def delete_comment(request, post_id: int, comment_id: int):
    post = get_object_or_404(Post, pk=post_id, is_deleted=False)
    c = get_object_or_404(PostComment, pk=comment_id, post=post)
    if c.author.user != request.user and not _can_moderate(request.user):
        return HttpResponseForbidden()
    c.is_deleted = True
    c.save(update_fields=["is_deleted"])

    post.comments_count = PostComment.objects.filter(post=post, is_deleted=False).count()
    post.save(update_fields=["comments_count"])

    return JsonResponse({"ok": True, "count": post.comments_count})


@login_required
@require_http_methods(["GET"])
def comments_more(request, post_id: int):
    post = get_object_or_404(Post, pk=post_id, is_deleted=False)
    try:
        offset = int(request.GET.get("offset", 0))
        limit = int(request.GET.get("limit", 10))
    except ValueError:
        offset, limit = 0, 10

    base_qs = (
        PostComment.objects
        .filter(post=post, is_deleted=False)
        .order_by("-created_at", "-id")
    )
    total = base_qs.count()
    comments = list(base_qs[offset: offset + limit])
    items = [serialize_comment(c, request) for c in comments]

    has_more = offset + limit < total
    next_offset = offset + limit
    return JsonResponse({"items": items, "has_more": has_more, "next_offset": next_offset})


@login_required
@permission_or_staff_required("base.moderate_posts")
@require_http_methods(["POST"])
def approve_post(request, post_id: int):
    post = get_object_or_404(Post, pk=post_id, is_deleted=False)
    post.is_approved = True
    post.approved_at = timezone.now()
    post.approved_by = request.user
    post.save(update_fields=["is_approved", "approved_at", "approved_by"])
    return JsonResponse({"ok": True, "post_id": post.id})


@login_required
@permission_or_staff_required("base.moderate_posts")
@require_http_methods(["POST"])
def reject_post(request, post_id: int):
    post = get_object_or_404(Post, pk=post_id, is_deleted=False)
    post.is_deleted = True
    post.save(update_fields=["is_deleted"])
    return JsonResponse({"ok": True, "post_id": post.id})
