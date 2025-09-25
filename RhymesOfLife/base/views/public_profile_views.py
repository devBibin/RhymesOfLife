from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from wagtail.models import Page

from blog.models import BlogIndexPage, BlogPage
from ..models import get_syndrome_choices
from base.models import Post

User = get_user_model()
SYNDROME_CHOICES = [(c, n) for c, n in get_syndrome_choices()]


def public_profile_view(request, username: str):
    user = get_object_or_404(User.objects.select_related("additional_info"), username=username)
    info = getattr(user, "additional_info", None)

    tab = request.GET.get("tab") or "articles"
    ap = int(request.GET.get("apage") or 1)
    pp = int(request.GET.get("ppage") or 1)

    articles_qs = BlogPage.objects.none()
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

    articles = Paginator(articles_qs, 10).get_page(ap)
    posts = Paginator(posts_qs, 10).get_page(pp)

    return render(
        request,
        "base/public_profile.html",
        {
            "profile_user": user,
            "info": info,
            "tab": tab if tab in ("articles", "posts") else "articles",
            "articles": articles,
            "posts": posts,
            "syndrome_choices": SYNDROME_CHOICES,
            "title": _("Profile"),
        },
    )
