from django.db import models
from django.contrib.auth import get_user_model
from wagtail.models import Page
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

from base.models import AdditionalUserInfo

User = get_user_model()


class HomePage(Page):
    intro = models.CharField(max_length=250, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
    ]


class BlogIndexPage(Page):
    intro = models.CharField(max_length=250, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        all_posts = (
            self.get_children()
            .live()
            .specific()
            .type(BlogPage)
            .order_by("-first_published_at")
        )
        context["posts"] = [p for p in all_posts if not p.is_deleted]
        return context


class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey('BlogPage', related_name='tagged_items', on_delete=models.CASCADE)


class BlogPage(Page):
    date = models.DateField("Дата публикации")
    author = models.ForeignKey(
        AdditionalUserInfo, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles'
    )
    intro = models.CharField("Краткое описание", max_length=250)
    main_image = models.ForeignKey(
        'wagtailimages.Image', null=True, blank=True, on_delete=models.SET_NULL, related_name='+'
    )

    body = RichTextField(verbose_name="Контент статьи")

    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    is_deleted = models.BooleanField(default=False)
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("author"),
        FieldPanel("intro"),
        FieldPanel("main_image"),
        FieldPanel("body"),
        FieldPanel("tags"),
    ]

    def is_editable_by(self, user):
        try:
            return self.author and self.author.user == user or user.is_superuser
        except AdditionalUserInfo.DoesNotExist:
            return False

    def is_liked_by(self, user):
        try:
            return self.likes.filter(author=user.additional_info, is_active=True).exists()
        except AdditionalUserInfo.DoesNotExist:
            return False

    def get_editor_config(self):
        return {
            'title': self.title,
            'intro': self.intro,
            'tags': ', '.join(self.tags.names()),
            'body': self.body.get_prep_value(),
            'main_image_id': self.main_image.id if self.main_image else None,
        }

    def get_template(self, request, *args, **kwargs):
        if request.GET.get('edit'):
            return 'blog/edit_article.html'
        return 'blog/blog_page.html'


class ArticleLike(models.Model):
    article = models.ForeignKey(
        BlogPage,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    author = models.ForeignKey(
        AdditionalUserInfo,
        on_delete=models.CASCADE
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('article', 'author')

    def __str__(self):
        return f"👍 {self.author.user.username} → {self.article.title}"


class ArticleComment(models.Model):
    article = models.ForeignKey(
        BlogPage,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        AdditionalUserInfo,
        on_delete=models.CASCADE
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"💬 {self.author.user.username}: {self.text[:30]}"
