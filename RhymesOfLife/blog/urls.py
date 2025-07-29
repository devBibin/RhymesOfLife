from django.urls import include, path
from .views import *
from wagtail.images import urls as wagtailimages_urls


urlpatterns = [
    path('new/', create_article_view, name='create_article'),
    path('<int:page_id>/edit/', edit_article_view, name='edit_article'),
    path('<int:page_id>/delete/', delete_article_view, name='delete_article'),
    path('<int:page_id>/like/', like_article_view, name='like_article'),
    path('<int:page_id>/comment/', comment_article_view, name='comment_article'),
    path('images/', include(wagtailimages_urls)),
]
