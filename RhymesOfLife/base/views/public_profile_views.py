from functools import lru_cache

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

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


@require_http_methods(["GET"])
def public_profile_view(request, username: str):
    user = get_object_or_404(User.objects.select_related("additional_info"), username=username)
    info = getattr(user, "additional_info", None)

    can_see_articles = bool(user.is_staff or user.is_superuser)

    tab_param = request.GET.get("tab")
    tab = tab_param if tab_param in ("articles", "posts") else ("articles" if can_see_articles else "posts")
    if not can_see_articles:
        tab = "posts"

    ap = _to_int(request.GET.get("apage"), 1)
    pp = _to_int(request.GET.get("ppage"), 1)

    articles_qs = BlogPage.objects.none()
    if can_see_articles:
        root = BlogIndexPage.objects.first()
        if root:
            articles_qs = (
                BlogPage.objects.live()
                .descendant_of(root)
                .filter(is_deleted=False, author=info, is_approved=True)
                .order_by("-date", "-first_published_at")
            )

    base_posts = (
        Post.objects
        .filter(author=info, is_deleted=False, is_hidden=False, is_hidden_by_reports=False)
        .select_related("author__user")
        .order_by("-created_at")
    )

    if request.user.is_authenticated and request.user == user:
        posts_qs = base_posts
    else:
        posts_qs = base_posts.filter(is_approved=True)

    posts_total = posts_qs.count()

    articles = Paginator(articles_qs, 10).get_page(ap) if can_see_articles else None
    posts = Paginator(posts_qs, 10).get_page(pp)

    liked_ids = []
    following_user_ids = []
    if request.user.is_authenticated and hasattr(request.user, "additional_info") and posts:
        me = request.user.additional_info
        liked_ids = list(
            PostLike.objects.filter(author=me, is_active=True, post__in=posts.object_list)
            .values_list("post_id", flat=True)
        )
        following_user_ids = list(
            me.following.filter(is_active=True).values_list("following__user_id", flat=True)
        )

    ctx = {
        "profile_user": user,
        "info": info,
        "tab": tab,
        "articles": articles,
        "posts": posts,
        "posts_total": posts_total,
        "liked_ids": liked_ids,
        "following_user_ids": following_user_ids,
        "can_see_articles": can_see_articles,
        "syndrome_choices": syndrome_choices(),
        "title": _("Profile"),
    }

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string("base/profile_content_fragment.html", ctx, request=request)
        return JsonResponse({"html": html})

    return render(request, "base/public_profile.html", ctx)
