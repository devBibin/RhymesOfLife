from __future__ import annotations

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.template.loader import render_to_string

from base.models import AdditionalUserInfo
from base.models import Post, PostImage, PostLike, PostComment
from base.utils.files import validate_mixed_upload

ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_SIDE_PX = 10_000
MAX_IMAGES_PER_POST = 10


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


def _feed_queryset(request):
    q = (request.GET.get("q") or "").strip()
    default_f = "mine" if request.user.is_authenticated else "latest"
    f = request.GET.get("filter", default_f)

    base = Post.objects.filter(is_deleted=False)
    published = base.filter(is_hidden=False, is_approved=True)

    if f == "mine" and request.user.is_authenticated:
        me = AdditionalUserInfo.objects.filter(user=request.user).first()
        qs = base.filter(author=me).order_by("-created_at")
    elif f == "subscriptions" and request.user.is_authenticated:
        me = AdditionalUserInfo.objects.filter(user=request.user).first()
        follow_ids = me.following.filter(is_active=True).values_list("following_id", flat=True)
        qs = published.filter(author__in=follow_ids).order_by("-created_at")
    elif f == "pending" and request.user.is_staff:
        qs = base.filter(is_approved=False).order_by("-created_at")
    else:
        f = "latest"
        qs = published.order_by("-created_at")

    if q:
        qs = qs.filter(Q(text__icontains=q) | Q(author__user__username__icontains=q))

    return f, qs


def _me(request):
    return AdditionalUserInfo.objects.filter(user=request.user).first() if request.user.is_authenticated else None


def feed(request):
    if not request.user.is_authenticated:
        return render(request, "base/home_public.html")

    f, qs = _feed_queryset(request)
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    liked_ids = []
    following_info_ids = set()
    following_user_ids = set()

    me = _me(request)
    if me:
        liked_ids = list(
            PostLike.objects.filter(author=me, is_active=True, post__in=page_obj.object_list)
            .values_list("post_id", flat=True)
        )
        following_info_ids = set(
            me.following.filter(is_active=True).values_list("following_id", flat=True)
        )
        following_user_ids = set(
            me.following.filter(is_active=True).values_list("following__user_id", flat=True)
        )

    context = {
        "posts": page_obj,
        "current_filter": f,
        "liked_ids": liked_ids,
        "following_info_ids": following_info_ids,
        "following_user_ids": following_user_ids,
    }

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string("base/post_list_fragment.html", context, request=request)
        return JsonResponse({"html": html})

    return render(request, "base/feed.html", context)


@login_required
@transaction.atomic
def create_post(request):
    if request.method != "POST":
        return render(request, "base/post_create.html")

    me = AdditionalUserInfo.objects.get(user=request.user)
    text = (request.POST.get("text") or "").strip()
    files = request.FILES.getlist("images")

    errors = _validate_images(files)
    if not text and not files:
        errors.append(_("Post must contain text or an image."))
    if errors:
        return render(request, "base/post_create.html", {"errors": errors, "text": text})

    post = Post.objects.create(
        author=me,
        text=text,
        is_approved=request.user.is_staff,
        approved_at=timezone.now() if request.user.is_staff else None,
        approved_by=request.user if request.user.is_staff else None,
    )

    for f in files:
        PostImage.objects.create(post=post, image=f)

    return redirect("home")


@login_required
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

        return redirect("home")

    return render(request, "base/post_edit.html", {"post": post})


@login_required
def hide_post(request, post_id: int):
    post = get_object_or_404(Post, pk=post_id, is_deleted=False)
    me = _me(request)
    if not me or (post.author_id != me.id and not request.user.is_superuser):
        return HttpResponseForbidden()
    post.is_hidden = True
    post.save(update_fields=["is_hidden"])
    return redirect("home")


@login_required
def unhide_post(request, post_id: int):
    post = get_object_or_404(Post, pk=post_id, is_deleted=False)
    me = _me(request)
    if not me or (post.author_id != me.id and not request.user.is_superuser):
        return HttpResponseForbidden()
    post.is_hidden = False
    post.save(update_fields=["is_hidden"])
    return redirect("home")


@login_required
def toggle_like(request, post_id: int):
    post = get_object_or_404(Post, pk=post_id, is_deleted=False)
    me = AdditionalUserInfo.objects.get(user=request.user)
    like, _ = PostLike.objects.get_or_create(post=post, author=me)
    like.is_active = not like.is_active
    like.save(update_fields=["is_active"])
    post.likes_count = PostLike.objects.filter(post=post, is_active=True).count()
    post.save(update_fields=["likes_count"])
    return JsonResponse({"likes": post.likes_count, "active": like.is_active})


@login_required
def add_comment(request, post_id: int):
    post = get_object_or_404(Post, pk=post_id, is_deleted=False)
    me = AdditionalUserInfo.objects.get(user=request.user)
    text = (request.POST.get("text") or "").strip()
    if not text:
        return JsonResponse({"error": "empty"}, status=400)
    c = PostComment.objects.create(post=post, author=me, text=text)
    post.comments_count = PostComment.objects.filter(post=post, is_deleted=False).count()
    post.save(update_fields=["comments_count"])
    return JsonResponse(
        {"id": c.id, "text": c.text, "author": request.user.username, "created": c.created_at.isoformat(), "post": post.id}
    )


@login_required
def delete_comment(request, post_id: int, comment_id: int):
    post = get_object_or_404(Post, pk=post_id, is_deleted=False)
    c = get_object_or_404(PostComment, pk=comment_id, post=post)
    if c.author.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden()
    c.is_deleted = True
    c.save(update_fields=["is_deleted"])
    post.comments_count = PostComment.objects.filter(post=post, is_deleted=False).count()
    post.save(update_fields=["comments_count"])
    return JsonResponse({"ok": True})


@user_passes_test(lambda u: u.is_staff)
def approve_post(request, post_id: int):
    post = get_object_or_404(Post, pk=post_id, is_deleted=False)
    post.is_approved = True
    post.approved_at = timezone.now()
    post.approved_by = request.user
    post.save(update_fields=["is_approved", "approved_at", "approved_by"])
    return redirect("home")


@user_passes_test(lambda u: u.is_staff)
def reject_post(request, post_id: int):
    post = get_object_or_404(Post, pk=post_id, is_deleted=False)
    post.is_deleted = True
    post.save(update_fields=["is_deleted"])
    return redirect("home")
