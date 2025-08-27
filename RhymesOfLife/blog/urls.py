from django.urls import include, path
from wagtail.images import urls as wagtailimages_urls
from .views import (
    create_article_view, edit_article_view, delete_article_view,
    like_article_view, comment_article_view, ajax_article_search,
    delete_comment_view, edit_comment_view, ckeditor5_upload,approve_article_view
)

urlpatterns = [
    path('new/', create_article_view, name='create_article'),
    path('<int:page_id>/edit/', edit_article_view, name='edit_article'),
    path('<int:page_id>/delete/', delete_article_view, name='delete_article'),

    path('<int:page_id>/like/', like_article_view, name='like_article'),
    path('<int:page_id>/comment/', comment_article_view, name='comment_article'),
    path('comment/<int:comment_id>/delete/', delete_comment_view, name='delete_comment'),
    path('comment/<int:comment_id>/edit/', edit_comment_view, name='edit_comment'),

    path('images/', include(wagtailimages_urls)),
    path('search/', ajax_article_search, name='ajax_article_search'),
    path("<int:page_id>/approve/", approve_article_view, name="approve_article"),

    path('upload/', ckeditor5_upload, name='ck5_upload'),
]
