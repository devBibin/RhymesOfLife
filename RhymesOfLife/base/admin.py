from django.contrib import admin
from .models import AdditionalUserInfo, ArticleLike, ArticleComment

@admin.register(AdditionalUserInfo)
class AdditionalUserInfoAdmin(admin.ModelAdmin):
    search_fields = ("user__username",)
    raw_id_fields = ["user",]
    list_display = ('user',)

@admin.register(ArticleLike)
class ArticleLikeAdmin(admin.ModelAdmin):
    list_display = ('user_info', 'get_username', 'article', 'created_at')
    search_fields = ('user_info__user__username', 'article__current_revision__title')
    list_filter = ('created_at',)
    raw_id_fields = ('user_info', 'article')
    
    def get_username(self, obj):
        return obj.user_info.user.username if obj.user_info else "No user"
    get_username.short_description = 'Username'
    get_username.admin_order_field = 'user_info__user__username'

@admin.register(ArticleComment)
class ArticleCommentAdmin(admin.ModelAdmin):
    list_display = ('user_info', 'get_username', 'article', 'created_at', 'short_text')
    search_fields = ('user_info__user__username', 'article__current_revision__title', 'text')
    list_filter = ('created_at',)
    raw_id_fields = ('user_info', 'article')
    
    def get_username(self, obj):
        return obj.user_info.user.username if obj.user_info else "No user"
    get_username.short_description = 'Username'
    get_username.admin_order_field = 'user_info__user__username'
    
    def short_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    short_text.short_description = 'Text'