from django import template
from ..models import ArticleLike

register = template.Library()

@register.simple_tag(takes_context=True)
def get_like_info(context, article):
    request = context['request']
    if request.user.is_authenticated:
        user_info = request.user.additional_info
        return {
            'user_liked': article.custom_fields.likes.filter(user_info=user_info, is_active=True).exists(),
            'active_likes_count': article.custom_fields.likes_count,
        }
    return {
        'user_liked': False,
        'active_likes_count': article.custom_fields.likes_count
    }

@register.filter
def is_view_page(path):
    return not any(p in path for p in ['_edit', '_create', '_delete', '_history','_plugin/attachments', '_settings', '_dir'])
