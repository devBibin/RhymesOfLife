from django.db import models
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext as _g
from django.utils.encoding import force_str

from wagtail.models import Page
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField

from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

from base.models import AdditionalUserInfo

User = get_user_model()


def _safe_username(aui):
    try:
        if not aui:
            return force_str(_g("unknown"))
        u = getattr(aui, "user", None)
        name = getattr(u, "username", None)
        return name or force_str(_g("unknown"))
    except Exception:
        return force_str(_g("unknown"))


class BlogIndexPage(Page):
    intro = models.CharField(_("Intro"), max_length=250, blank=True)
    posts_per_page = 10

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    def get_context(self, request):
        context = super().get_context(request)

        base_live = (
            BlogPage.objects.live()
            .descendant_of(self)
            .filter(is_deleted=False)
        )
        published = base_live.filter(is_approved=True)

        if request.user.is_authenticated:
            mine = (
                BlogPage.objects.descendant_of(self)
                .filter(author__user=request.user, is_deleted=False)
            )
        else:
            mine = BlogPage.objects.none()

        f = request.GET.get("filter", "popular")
        q = request.GET.get("q", "").strip()

        if f == "popular":
            qs = published.order_by("-likes_count")
        elif f == "mine":
            qs = mine.order_by("-latest_revision_created_at")
        elif f == "subscriptions" and request.user.is_authenticated:
            f_ids = (
                request.user.additional_info.following
                .filter(is_active=True)
                .values_list("following_id", flat=True)
            )
            qs = published.filter(author__in=f_ids).order_by("-first_published_at")
        elif f == "doctors":
            qs = published.filter(author__user__is_staff=True).order_by("-first_published_at")
        elif f == "pending" and request.user.is_staff:
            qs = base_live.filter(is_approved=False, is_rejected=False).order_by("-first_published_at")
        else:
            f = "popular"
            qs = published.order_by("-likes_count")

        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(tags__name__icontains=q)
                | Q(author__first_name__icontains=q)
                | Q(author__last_name__icontains=q)
            ).distinct()

        paginator = Paginator(qs, self.posts_per_page)
        page_num = request.GET.get("page")
        page_obj = paginator.get_page(page_num)

        context.update(
            {
                "posts": page_obj,
                "current_filter": f,
                "query": q,
            }
        )
        return context

    def serve(self, request, *args, **kwargs):
        translation.activate(request.LANGUAGE_CODE)
        request.LANGUAGE_CODE = translation.get_language()
        context = self.get_context(request)
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            html = render_to_string(
                "blog/includes/article_list_fragment.html",
                context,
                request=request,
            )
            return JsonResponse({"html": html})
        return TemplateResponse(request, self.get_template(request), context)


class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey(
        "BlogPage", related_name="tagged_items", on_delete=models.CASCADE
    )


class BlogPage(Page):
    date = models.DateField(_("Publication date"))
    author = models.ForeignKey(
        AdditionalUserInfo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
        verbose_name=_("Author"),
    )
    intro = models.CharField(_("Short description"), max_length=250)
    main_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Main image"),
    )
    body = RichTextField(verbose_name=_("Article content"))

    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    is_deleted = models.BooleanField(_("Soft-deleted"), default=False)
    likes_count = models.PositiveIntegerField(_("Likes count"), default=0)
    comments_count = models.PositiveIntegerField(_("Comments count"), default=0)

    is_approved = models.BooleanField(_("Approved by admin"), default=False, db_index=True)
    approved_at = models.DateTimeField(_("Approved at"), null=True, blank=True)
    approved_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="approved_articles", verbose_name=_("Approved by")
    )

    is_rejected = models.BooleanField(_("Rejected by admin"), default=False, db_index=True)
    rejected_at = models.DateTimeField(_("Rejected at"), null=True, blank=True)
    rejected_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="rejected_articles", verbose_name=_("Rejected by")
    )

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("author"),
        FieldPanel("intro"),
        FieldPanel("main_image"),
        FieldPanel("body"),
        FieldPanel("tags"),
        FieldPanel("is_approved"),
        FieldPanel("is_rejected"),
    ]

    @property
    def is_draft(self):
        return not self.live

    def serve(self, request, *args, **kwargs):
        translation.activate(request.LANGUAGE_CODE)
        request.LANGUAGE_CODE = translation.get_language()

        if self.is_draft:
            if request.user.is_authenticated and self.author and self.author.user == request.user:
                return TemplateResponse(request, self.get_template(request), {"page": self})
            if request.user.is_staff:
                return TemplateResponse(request, self.get_template(request), {"page": self})
            raise Http404

        if not self.is_approved:
            if request.user.is_authenticated and self.author and self.author.user == request.user:
                return TemplateResponse(request, self.get_template(request), {"page": self})
            if request.user.is_staff:
                return TemplateResponse(request, self.get_template(request), {"page": self})
            raise Http404

        return TemplateResponse(request, self.get_template(request), {"page": self})

    def is_editable_by(self, user):
        try:
            return (self.author and self.author.user == user) or user.is_superuser
        except AdditionalUserInfo.DoesNotExist:
            return False

    def is_liked_by(self, user):
        try:
            return self.likes.filter(author=user.additional_info, is_active=True).exists()
        except AdditionalUserInfo.DoesNotExist:
            return False

    def get_editor_config(self):
        return {
            "title": self.title,
            "intro": self.intro,
            "tags": ", ".join(self.tags.names()),
            "body": self.body.get_prep_value(),
            "main_image_id": self.main_image.id if self.main_image else None,
        }

    def get_template(self, request, *args, **kwargs):
        if request.GET.get("edit"):
            return "blog/edit_article.html"
        return "blog/blog_page.html"

    @property
    def visible_comments(self):
        return self.comments.filter(is_deleted=False)

    def get_context(self, request, *args, **kwargs):
        ctx = super().get_context(request, *args, **kwargs)
        me = getattr(getattr(request, "user", None), "additional_info", None)
        if me:
            ctx["following_user_ids"] = list(
                me.following.filter(is_active=True).values_list("following__user_id", flat=True)
            )
        return ctx

    @property
    def is_pending(self):
        return self.live and not self.is_deleted and not self.is_approved and not self.is_rejected


class ArticleLike(models.Model):
    article = models.ForeignKey(BlogPage, on_delete=models.CASCADE, related_name="likes")
    author = models.ForeignKey(AdditionalUserInfo, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("article", "author")
        verbose_name = _("Article like")
        verbose_name_plural = _("Article likes")

    def __str__(self):
        return force_str(f"👍 {_safe_username(self.author)} → {getattr(self.article, 'title', '')}")


class ArticleComment(models.Model):
    article = models.ForeignKey(BlogPage, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(AdditionalUserInfo, on_delete=models.CASCADE)
    text = models.TextField(_("Text"))
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    edited_at = models.DateTimeField(_("Edited at"), null=True, blank=True)
    is_deleted = models.BooleanField(_("Soft-deleted"), default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Article comment")
        verbose_name_plural = _("Article comments")

    def __str__(self):
        if self.is_deleted:
            return force_str(_g("🗑 Deleted comment"))
        return force_str(f"💬 {_safe_username(self.author)}: {(self.text or '')[:30]}")
