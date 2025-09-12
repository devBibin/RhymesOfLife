from django.contrib import admin
from .models import *


@admin.register(ArticleComment)
class ArticleComment(admin.ModelAdmin):
    pass


@admin.register(ArticleLike)
class ArticleLike(admin.ModelAdmin):
    pass

@admin.register(BlogPage)
class BlogPage(admin.ModelAdmin):
    pass
