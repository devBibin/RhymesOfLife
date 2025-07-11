from django.urls import path
from . import views
from .views import profile_edit_view, resend_verification_view

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify/<uidb64>/<token>/', views.verify_email_view, name='verify_email'),
    path('request-verification/', views.request_verification_view, name='request_verification'),
    path("profile/edit/", profile_edit_view, name="profile_edit"),
    path('article/<int:article_id>/comment/', views.post_comment, name='wiki_post_comment'),
    path('article/<int:article_id>/like/', views.toggle_like, name='wiki_toggle_like'),
    path('', views.home_view, name='home'),
]
