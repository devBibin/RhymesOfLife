from django.urls import path

from .views.telegram_views import (
    connect_telegram_view,
    telegram_webhook,
)

from .views.auth_views import (
    register_view,
    login_view,
    logout_view,
    verify_email_view,
    verify_prompt_view,
    request_verification_view,
    home_public_view,
    phone_enter_view,
    phone_wait_view,
    phone_status_api,
    phone_change_view,
    consents_view,
)
from .views.profile_views import (
    profile_view,
    profile_edit_view,
    profile_onboarding_view,
)
from .views.documents_views import (
    my_documents_view,
    exam_detail_api,
    delete_document_api,
    recommendations_view,
)
from .views.doctors_views import (
    patients_list_view,
    patient_exams_view,
)
from .views.social_views import (
    follow_view,
    unfollow_view,
    notifications_view,
)

from .views.auth_reset_views import (
    password_reset_request_view,
    password_reset_verify_view,
    password_reset_new_view,
)

from base.views.feed_views import (
    feed, create_post, edit_post, hide_post, unhide_post,
    toggle_like, add_comment, delete_comment,
    approve_post, reject_post,
)


urlpatterns = [
    path("", feed, name="home"),
    path("welcome/", home_public_view, name="home_public"),

    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),

    path("verify/", verify_prompt_view, name="verify_prompt"),
    path("verify/request/", request_verification_view, name="request_verification"),
    path("verify/<uidb64>/<token>/", verify_email_view, name="verify_email"),

    path("auth/phone/", phone_enter_view, name="phone_enter"),
    path("auth/phone/wait/", phone_wait_view, name="phone_wait"),
    path("auth/phone/status/", phone_status_api, name="phone_status_api"),
    path("auth/phone/change/", phone_change_view, name="phone_change"),

    path("consents/", consents_view, name="consents"),

    path("profile/", profile_view, name="my_profile"),
    path("profile/edit/", profile_edit_view, name="profile_edit"),
    path("profile/<str:username>/", profile_view, name="user_profile"),
    path("onboarding/profile/", profile_onboarding_view, name="profile_onboarding"),

    path("my-documents/", my_documents_view, name="my_documents"),
    path("api/exams/<int:exam_id>/", exam_detail_api, name="exam_detail_api"),
    path("api/documents/<int:doc_id>/", delete_document_api, name="delete_document_api"),

    path("recommendations/", recommendations_view, name="recommendations"),

    path("patients/", patients_list_view, name="patients_list"),
    path("patients/<int:user_id>/", patient_exams_view, name="patient_exams"),

    path("notifications/", notifications_view, name="notifications"),
    path("follow/<int:user_id>/", follow_view, name="follow_user"),
    path("unfollow/<int:user_id>/", unfollow_view, name="unfollow_user"),

    path("connect-telegram/", connect_telegram_view, name="connect_telegram"),
    path("telegram/webhook/<str:bot_token>/", telegram_webhook, name="telegram_webhook"),

    path("password/reset/", password_reset_request_view, name="password_reset_request"),
    path("password/reset/verify/", password_reset_verify_view, name="password_reset_verify"),
    path("password/reset/new/", password_reset_new_view, name="password_reset_new"),

    path("posts/create/", create_post, name="post_create"),
    path("posts/<int:post_id>/edit/", edit_post, name="post_edit"),
    path("posts/<int:post_id>/hide/", hide_post, name="post_hide"),
    path("posts/<int:post_id>/unhide/", unhide_post, name="post_unhide"),
    path("posts/<int:post_id>/like/", toggle_like, name="post_like"),
    path("posts/<int:post_id>/comments/add/", add_comment, name="post_comment_add"),
    path("posts/<int:post_id>/comments/<int:comment_id>/delete/", delete_comment, name="post_comment_delete"),
    path("posts/<int:post_id>/approve/", approve_post, name="post_approve"),
    path("posts/<int:post_id>/reject/", reject_post, name="post_reject"),
]
