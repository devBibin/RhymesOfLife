from functools import lru_cache

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from wagtail.models import Page  # keeps Wagtail registry loaded
from blog.models import BlogIndexPage, BlogPage
from base.models import Post, PostLike
from ..models import get_syndrome_choices

User = get_user_model()


@lru_cache(maxsize=1)
def syndrome_choices():
    return [(c, n) for c, n in get_syndrome_choices()]


def _to_int(value, default=1):
    try:
        return int(value)
    except Exception:
        return default


def public_profile_view(request, username: str):
    user = get_object_or_404(User.objects.select_related("additional_info"), username=username)
    info = getattr(user, "additional_info", None)

    can_see_articles = bool(
        user.is_staff
        or user.is_superuser
        or (request.user.is_authenticated and request.user.is_staff)
    )

    tab = request.GET.get("tab") or ("articles" if can_see_articles else "posts")
    ap = _to_int(request.GET.get("apage"), 1)
    pp = _to_int(request.GET.get("ppage"), 1)

    articles_qs = BlogPage.objects.none()
    if can_see_articles:
        root = BlogIndexPage.objects.first()
        if root:
            articles_qs = (
                BlogPage.objects.live()
                .descendant_of(root)
                .filter(is_deleted=False, is_approved=True, author=info)
                .order_by("-date", "-first_published_at")
            )

    posts_qs = (
        Post.objects.filter(author=info, is_deleted=False, is_hidden=False, is_approved=True)
        .select_related("author__user")
        .order_by("-created_at")
    )
    posts_total = posts_qs.count()

    articles = Paginator(articles_qs, 10).get_page(ap) if can_see_articles else None
    posts = Paginator(posts_qs, 10).get_page(pp)

    liked_ids = []
    following_user_ids = []
    if request.user.is_authenticated and hasattr(request.user, "additional_info"):
        me = request.user.additional_info
        liked_ids = list(
            PostLike.objects.filter(author=me, is_active=True, post__in=posts.object_list)
            .values_list("post_id", flat=True)
        )
        following_user_ids = list(
            me.following.filter(is_active=True).values_list("following__user_id", flat=True)
        )

    return render(
        request,
        "base/public_profile.html",
        {
            "profile_user": user,
            "info": info,
            "tab": tab if tab in ("articles", "posts") else ("articles" if can_see_articles else "posts"),
            "articles": articles,
            "posts": posts,
            "posts_total": posts_total,
            "liked_ids": liked_ids,
            "following_user_ids": following_user_ids,
            "can_see_articles": can_see_articles,
            "syndrome_choices": syndrome_choices(),
            "title": _("Profile"),
        },
    )
