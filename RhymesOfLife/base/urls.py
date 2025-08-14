from django.urls import path
from . import views
from .views import *


urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('verify/<uidb64>/<token>/', verify_email_view, name='verify_email'),
    path('request-verification/', request_verification_view, name='request_verification'),
    path("profile/edit/", profile_edit_view, name="profile_edit"),
    path("profile/", profile_view, name="my_profile"),
    path("profile/<str:username>/", profile_view, name="user_profile"),
    path('my-documents/', my_documents_view, name='my_documents'),
    path('api/exams/<int:exam_id>/', exam_detail_api, name='exam_detail_api'),
    path('api/documents/<int:doc_id>/', delete_document_api, name='delete_document_api'),
    path("patients/", patients_list_view, name="patients_list"),
    path("patients/<int:user_id>/", patient_exams_view, name="patient_exams"),
    path('notifications/', notifications_view, name='notifications'),
    path('follow/<int:user_id>/', follow_view, name='follow_user'),
    path('unfollow/<int:user_id>/', unfollow_view, name='unfollow_user'),


    path('', views.home_view, name='home'),
]
