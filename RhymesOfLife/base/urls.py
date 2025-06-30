from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify/<uidb64>/<token>/', views.verify_email_view, name='verify_email'),
    path('request-verification/', views.request_verification_view, name='request_verification'),
    path('', views.home_view, name='home'),
]
