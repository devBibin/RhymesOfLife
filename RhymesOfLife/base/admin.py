from django.contrib import admin
from .models import *


@admin.register(AdditionalUserInfo)
class AdditionalUserInfoAdmin(admin.ModelAdmin):
    search_fields = ("user__username",)
    raw_id_fields = ["user",]
    list_display = ('user',)

@admin.register(ArticleLike)
class ArticleLikeAdmin(admin.ModelAdmin):
    pass

@admin.register(ArticleComment)
class ArticleCommentAdmin(admin.ModelAdmin):
    pass

@admin.register(CustomArticle)
class CustomArticle(admin.ModelAdmin):
    pass