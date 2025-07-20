from django.urls import path
from . import views
from .views import profile_edit_view, get_article_comments, profile_view, my_documents_view,exam_detail_api, delete_document_api

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify/<uidb64>/<token>/', views.verify_email_view, name='verify_email'),
    path('request-verification/', views.request_verification_view, name='request_verification'),
    path("profile/edit/", profile_edit_view, name="profile_edit"),
    path('article/<int:article_id>/comment/', views.post_comment, name='wiki_post_comment'),
    path('article/<int:article_id>/like/', views.toggle_like, name='wiki_toggle_like'),
    path('articles/<int:article_id>/comments/', get_article_comments, name='wiki_get_comments'),
    path("profile/", profile_view, name="my_profile"),
    path("profile/<str:username>/", profile_view, name="user_profile"),
    path('my-documents/', my_documents_view, name='my_documents'),
    path('api/exams/<int:exam_id>/', exam_detail_api, name='exam_detail_api'),
    path('api/documents/<int:doc_id>/', delete_document_api, name='delete_document_api'),
    path('', views.home_view, name='home'),
]
