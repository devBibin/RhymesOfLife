from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods, require_POST
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage

from wagtail.models import Page
from wagtail.images import get_image_model

from .models import BlogPage, BlogIndexPage, ArticleLike, ArticleComment
from .constants import PREDEFINED_TAGS

import bleach

from base.utils.files import validate_image_upload
from base.utils.logging import get_app_logger

from PIL import Image as PILImage, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = False
PILImage.MAX_IMAGE_PIXELS = 10000 * 10000

log = get_app_logger(__name__)

ALLOWED_EXTS = set(getattr(settings, "WAGTAILIMAGES_EXTENSIONS", ["gif", "jpg", "jpeg", "png", "webp"]))
MAX_UPLOAD = int(getattr(settings, "WAGTAILIMAGES_MAX_UPLOAD_SIZE", 10 * 1024 * 1024))
ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}

ALLOWED_TAGS = [
    "p", "br", "strong", "em", "u", "s", "a", "ul", "ol", "li", "blockquote", "code", "pre", "hr",
    "h2", "h3", "h4", "h5", "h6", "figure", "figcaption", "img",
    "table", "thead", "tbody", "tr", "th", "td",
]
ALLOWED_ATTRS = {
    "*": ["class", "style"],
    "a": ["href", "title", "rel", "target"],
    "img": ["src", "alt", "width", "height", "loading", "class", "style"],
    "table": ["border", "style"],
    "th": ["colspan", "rowspan", "style"],
    "td": ["colspan", "rowspan", "style"],
}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


staff_required = user_passes_test(lambda u: (u.is_staff or u.is_superuser))


def _sanitize_html(html: str) -> str:
    return bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, protocols=ALLOWED_PROTOCOLS, strip=True)


def _get_or_create_blog_index():
    root = Page.get_first_root_node()
    parent = BlogIndexPage.objects.first()
    if not parent:
        parent = BlogIndexPage(title="Blog", slug="blog")
        root.add_child(instance=parent)
        parent.save_revision().publish()
        log.info("BlogIndexPage created: id=%s", parent.id)
    return parent


def _latest_revision_specific(page):
    try:
        if hasattr(page, "get_latest_revision_as_page"):
            obj = page.get_latest_revision_as_page()
            if obj:
                return getattr(obj, "specific", obj)
    except Exception:
        pass
    try:
        rev = page.get_latest_revision()
        if not rev:
            return page
        if hasattr(rev, "as_object"):
            obj = rev.as_object()
        elif hasattr(rev, "as_page_object"):
            obj = rev.as_page_object()
        else:
            return page
        return getattr(obj, "specific", obj)
    except Exception:
        return page


def _unique_slug(base: str) -> str:
    if not base:
        base = str(int(timezone.now().timestamp()))
    slug = base
    i = 1
    while BlogPage.objects.filter(slug=slug).exists():
        slug = f"{base}-{i}"
        i += 1
    return slug


def _filter_tags_to_predefined(tags):
    allowed = set(PREDEFINED_TAGS)
    return [t for t in tags if t in allowed]


@login_required
@staff_required
@require_http_methods(["GET", "POST"])
def create_article_view(request):
    ctx = {"all_tags": PREDEFINED_TAGS}
    if request.method == "POST":
        action = request.POST.get("action") or "draft"
        title = request.POST.get("title", "").strip()
        intro = request.POST.get("intro", "").strip()
        body = _sanitize_html(request.POST.get("body", "").strip())
        tags = _filter_tags_to_predefined(request.POST.getlist("tags"))
        main_img_f = request.FILES.get("main_image")

        ctx.update({"title": title, "intro": intro, "body": body, "selected_tags": tags})

        try:
            if not title or not body:
                raise ValidationError(_("Title and content are required."))

            with transaction.atomic():
                main_image = None
                if main_img_f:
                    ok, err = validate_image_upload(
                        main_img_f,
                        max_size_bytes=MAX_UPLOAD,
                        max_side_px=10000,
                        allowed_mimes=ALLOWED_IMAGE_MIMES,
                        allowed_formats=ALLOWED_IMAGE_FORMATS,
                        max_total_pixels=10000 * 10000,
                    )
                    if not ok:
                        raise ValidationError(_(err))

                    Image = get_image_model()
                    main_image = Image.objects.create(
                        title=f"{title[:50]} — main image",
                        file=main_img_f,
                        uploaded_by_user=request.user,
                    )

                parent = _get_or_create_blog_index()
                unique_slug = _unique_slug(slugify(title, allow_unicode=True))

                page = BlogPage(
                    title=title,
                    slug=unique_slug,
                    date=timezone.now(),
                    intro=intro,
                    author=request.user.additional_info,
                    main_image=main_image,
                    body=body,
                )
                parent.add_child(instance=page)
                if tags:
                    page.tags.add(*tags)
                rev = page.save_revision()
                if action == "publish":
                    rev.publish()
                    log.info("Article published: page_id=%s author_id=%s", page.id, request.user.id)
                    return redirect(page.url)
                else:
                    if page.live:
                        page.unpublish()
                    log.info("Article saved as draft: page_id=%s author_id=%s", page.id, request.user.id)
                    return redirect(f"{reverse('edit_article', args=[page.id])}?edit=1")

        except ValidationError as e:
            ctx["error"] = str(e)
            log.warning("Create article validation error: user_id=%s reason=%s", request.user.id, e)
        except Exception as e:
            ctx["error"] = _("System error: %(msg)s") % {"msg": e}
            log.exception("Create article system error: user_id=%s", request.user.id)

    return render(request, "blog/create_article.html", ctx)


@login_required
@staff_required
@require_http_methods(["GET", "POST"])
def edit_article_view(request, page_id):
    page = get_object_or_404(BlogPage, id=page_id).specific
    if not page.is_editable_by(request.user):
        return HttpResponseForbidden()

    if request.method == "POST":
        try:
            action = request.POST.get("action", "publish")
            page.title = request.POST.get("title", page.title).strip()
            page.intro = request.POST.get("intro", page.intro).strip()
            page.body = _sanitize_html(request.POST.get("body", page.body).strip())
            page.tags.set(_filter_tags_to_predefined(request.POST.getlist("tags")))

            if "main_image" in request.FILES:
                f = request.FILES["main_image"]
                ok, err = validate_image_upload(
                    f,
                    max_size_bytes=MAX_UPLOAD,
                    max_side_px=10000,
                    allowed_mimes=ALLOWED_IMAGE_MIMES,
                    allowed_formats=ALLOWED_IMAGE_FORMATS,
                    max_total_pixels=10000 * 10000,
                )
                if not ok:
                    raise ValidationError(_(err))

                Image = get_image_model()
                if page.main_image:
                    page.main_image.delete()
                page.main_image = Image.objects.create(
                    title=f"{page.title[:50]} — main image",
                    file=f,
                    uploaded_by_user=request.user,
                )
            elif request.POST.get("main_image-clear") == "on" and page.main_image:
                page.main_image.delete()
                page.main_image = None

            rev = page.save_revision()
            if action == "publish":
                rev.publish()
                log.info("Article republished: page_id=%s editor_id=%s", page.id, request.user.id)
                return redirect(page.url)
            else:
                log.info("Article saved draft: page_id=%s editor_id=%s", page.id, request.user.id)
                return redirect(f"{reverse('edit_article', args=[page.id])}?edit=1")

        except ValidationError as e:
            error = str(e)
            log.warning("Edit article validation error: page_id=%s user_id=%s reason=%s", page.id, request.user.id, e)
        except Exception as e:
            error = _("System error: %(msg)s") % {"msg": e}
            log.exception("Edit article system error: page_id=%s user_id=%s", page.id, request.user.id)

        page_for_form = _latest_revision_specific(page)
        ctx = {
            "page": page_for_form,
            "all_tags": PREDEFINED_TAGS,
            "selected_tags": list(page_for_form.tags.names()),
            "error": error,
        }
        return render(request, "blog/edit_article.html", ctx)

    page_for_form = _latest_revision_specific(page) if (page.has_unpublished_changes or not page.live) else page
    ctx = {"page": page_for_form, "all_tags": PREDEFINED_TAGS, "selected_tags": list(page_for_form.tags.names())}
    return render(request, "blog/edit_article.html", ctx)


@login_required
@staff_required
@require_POST
def delete_article_view(request, page_id):
    page = get_object_or_404(BlogPage, id=page_id).specific
    if not page.is_editable_by(request.user):
        return HttpResponseForbidden(_("Insufficient permissions."))
    if page.live:
        page.is_deleted = True
        page.save_revision().publish()
        log.info("Article soft-deleted: page_id=%s user_id=%s", page.id, request.user.id)
    else:
        pid = page.id
        page.delete()
        log.info("Article hard-deleted: page_id=%s user_id=%s", pid, request.user.id)
    return redirect("/articles/")


@login_required
@require_POST
def like_article_view(request, page_id):
    page = get_object_or_404(BlogPage, id=page_id).specific
    user_info = request.user.additional_info

    like, created = ArticleLike.objects.get_or_create(
        author=user_info, article=page, defaults={"is_active": True}
    )
    if not created:
        like.is_active = not like.is_active
        like.save(update_fields=["is_active"])

    page.likes_count = ArticleLike.objects.filter(article=page, is_active=True).count()
    page.save(update_fields=["likes_count"])

    log.info("Article like toggled: page_id=%s user_id=%s liked=%s", page.id, request.user.id, like.is_active)
    return JsonResponse({"liked": like.is_active, "like_count": page.likes_count})


@login_required
@require_POST
def comment_article_view(request, page_id):
    text = request.POST.get("text", "").strip()
    if not text:
        return JsonResponse({"error": _("Comment cannot be empty.")}, status=400)

    page = get_object_or_404(BlogPage, id=page_id).specific
    user_info = request.user.additional_info

    comment = ArticleComment.objects.create(article=page, author=user_info, text=text)

    page.comments_count = ArticleComment.objects.filter(article=page, is_deleted=False).count()
    page.save(update_fields=["comments_count"])

    log.info("Article comment added: page_id=%s user_id=%s comment_id=%s", page.id, request.user.id, comment.id)
    return JsonResponse({
        "id": comment.id,
        "username": user_info.first_name or request.user.username,
        "avatar": user_info.avatar.url if user_info.avatar else "",
        "text": comment.text,
        "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M"),
        "comment_count": page.comments_count,
    })


def ajax_article_search(request):
    query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "date").strip()
    page_num = request.GET.get("page", "1")
    blog_index = BlogIndexPage.objects.first()

    results = BlogPage.objects.none()
    if blog_index:
        results = (
            BlogPage.objects.live()
            .descendant_of(blog_index)
            .filter(is_deleted=False, is_approved=True)
        )

    if query:
        results = results.filter(
            Q(title__icontains=query)
            | Q(tags__name__icontains=query)
            | Q(author__first_name__icontains=query)
            | Q(author__last_name__icontains=query)
        ).distinct()

    if sort == "popular":
        results = results.order_by("-likes_count", "-date")
    else:
        results = results.order_by("-date", "-likes_count")

    paginator = Paginator(results, 10)
    try:
        page_obj = paginator.page(page_num)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    html = render_to_string(
        "blog/includes/article_list_fragment.html",
        {"posts": page_obj, "sort": sort, "query": query},
        request=request,
    )
    return JsonResponse({"html": html})


@login_required
@require_POST
def delete_comment_view(request, comment_id):
    comment = get_object_or_404(ArticleComment, id=comment_id)
    if comment.author.user != request.user and not request.user.is_superuser:
        return HttpResponseForbidden(_("You cannot delete someone else's comment."))

    comment.is_deleted = True
    comment.save(update_fields=["is_deleted"])

    article = comment.article
    article.comments_count = ArticleComment.objects.filter(article=article, is_deleted=False).count()
    article.save(update_fields=["comments_count"])

    log.info("Article comment deleted: comment_id=%s user_id=%s", comment.id, request.user.id)
    return JsonResponse({"deleted": True, "comment_count": article.comments_count})


@login_required
@require_http_methods(["POST"])
def edit_comment_view(request, comment_id):
    comment = get_object_or_404(ArticleComment, id=comment_id)
    if comment.author.user != request.user and not request.user.is_superuser:
        return HttpResponseForbidden(_("You cannot edit someone else's comment."))

    new_text = request.POST.get("text", "").strip()
    if not new_text:
        return JsonResponse({"error": _("Comment cannot be empty.")}, status=400)

    comment.text = new_text
    comment.edited_at = timezone.now()
    comment.save(update_fields=["text", "edited_at"])

    log.info("Article comment edited: comment_id=%s user_id=%s", comment.id, request.user.id)
    return JsonResponse({"text": comment.text, "edited_at": comment.edited_at.strftime("%Y-%m-%d %H:%M")})


@login_required
@staff_required
@require_POST
def ckeditor5_upload(request):
    f = request.FILES.get("upload")
    if not f:
        return JsonResponse({"error": {"message": _("No file uploaded.")}}, status=400)
    try:
        ok, err = validate_image_upload(
            f,
            max_size_bytes=MAX_UPLOAD,
            max_side_px=10000,
            allowed_mimes=ALLOWED_IMAGE_MIMES,
            allowed_formats=ALLOWED_IMAGE_FORMATS,
            max_total_pixels=10000 * 10000,
        )
        if not ok:
            return JsonResponse({"error": {"message": _(err)}}, status=400)

        ImageModel = get_image_model()
        image = ImageModel(file=f, title=f.name, uploaded_by_user=request.user)
        image.save()
        try:
            rendition = image.get_rendition("max-1600x1600|format-webp")
        except Exception:
            rendition = image.get_rendition("max-1600x1600")
        log.info("CKEditor image uploaded: image_id=%s user_id=%s", image.id, request.user.id)
        return JsonResponse({"url": rendition.url})
    except Exception:
        log.exception("CKEditor upload error: user_id=%s", request.user.id)
        return JsonResponse({"error": {"message": _("Upload error.")}}, status=500)


@login_required
@require_POST
@user_passes_test(lambda u: u.is_staff)
def approve_article_view(request, page_id):
    page = get_object_or_404(BlogPage, id=page_id).specific
    page.is_approved = True
    page.approved_at = timezone.now()
    page.approved_by = request.user
    page.save(update_fields=["is_approved", "approved_at", "approved_by"])
    return redirect(page.url)


@login_required
@require_POST
@user_passes_test(lambda u: u.is_staff)
def reject_article_view(request, page_id):
    page = get_object_or_404(BlogPage, id=page_id).specific
    page.is_approved = False
    page.approved_at = None
    page.approved_by = None
    page.is_rejected = True
    page.rejected_at = timezone.now()
    page.rejected_by = request.user
    page.save(update_fields=[
        "is_approved", "approved_at", "approved_by",
        "is_rejected", "rejected_at", "rejected_by",
    ])
    referer = request.META.get("HTTP_REFERER")
    return redirect(referer or reverse("edit_article", args=[page.id]))
