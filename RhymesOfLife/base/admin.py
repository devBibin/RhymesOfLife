from django.contrib import admin
from .models import AdditionalUserInfo, ArticleLike, ArticleComment

@admin.register(AdditionalUserInfo)
class AdditionalUserInfoAdmin(admin.ModelAdmin):
    search_fields = ("user__username", )
    raw_id_fields = ["user", ]

@admin.register(ArticleLike)
class ArticleLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'article', 'created_at')
    search_fields = ('user__username', 'article__current_revision__title')
    list_filter = ('created_at',)

@admin.register(ArticleComment)
class ArticleCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'article', 'created_at', 'text')
    search_fields = ('user__username', 'article__current_revision__title', 'text')
    list_filter = ('created_at',)
