from django.urls import path

from .views.telegram_views import (
    connect_telegram_view,
    telegram_webhook,
    telegram_unlink_view,
    telegram_regenerate_link_view,
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
    info_ndst,
    info_sed,
    info_marfan,
    info_sld,
    auth_combined_view
)
from .views.profile_views import (
    profile_view,
    profile_edit_view,
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
    approve_post, reject_post, comments_more,
    report_post,
)

from .views.language_views import (
    set_language
)

from .views.public_profile_views import (
    public_profile_view
)

from .views.admin_notifications import (
    admin_notify_page, admin_notify_api,
    admin_user_suggest,
)

from .views.help_request_views import (
    help_request_view, staff_help_requests_page,
    staff_help_requests_api, staff_help_requests_data,
)

from .views.wellness_views import (
    my_wellness_view,
    wellness_entries_api,
    wellness_settings_api,
)
from .views.doctors_wellness_views import (
    patient_wellness_view,
)

from .views.users_views import (
    set_user_censorship, toggle_user_ban,
)

from .views.account_restrictions import (
    banned_view
    )

from .views.health_views import (
    my_health_view,
    health_documents_partial,
    health_recommendations_partial,
    health_wellness_partial,
)

urlpatterns = [
    path("ma/", feed, name="home"),
    path("", home_public_view, name="home_public"),
    path("ndst/", info_ndst, name="info_ndst"),
    path("sed/", info_sed, name="info_sed"),
    path("marfan/", info_marfan, name="info_marfan"),
    path("sld/", info_sld, name="info_sld"),

    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("auth/", auth_combined_view, name="auth_combined"),

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
    path("u/<str:username>/", public_profile_view, name="public_profile"),

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
    path("telegram/regenerate/", telegram_regenerate_link_view, name="telegram_regenerate"),
    path("telegram/webhook/<str:bot_token>/", telegram_webhook, name="telegram_webhook"),
    path("telegram/unlink/", telegram_unlink_view, name="telegram_unlink"),

    path("password/reset/", password_reset_request_view, name="password_reset_request"),
    path("password/reset/verify/", password_reset_verify_view, name="password_reset_verify"),
    path("password/reset/new/", password_reset_new_view, name="password_reset_new"),

    path("posts/create/", create_post, name="post_create"),
    path("posts/<int:post_id>/edit/", edit_post, name="post_edit"),
    path("posts/<int:post_id>/hide/", hide_post, name="post_hide"),
    path("posts/<int:post_id>/unhide/", unhide_post, name="post_unhide"),
    path("posts/<int:post_id>/like/", toggle_like, name="post_like"),
    path("posts/<int:post_id>/comments/add/", add_comment, name="post_comment_add"),
    path("posts/<int:post_id>/comments/", comments_more, name="post_comments_more"),
    path("posts/<int:post_id>/comments/<int:comment_id>/delete/", delete_comment, name="post_comment_delete"),
    path("posts/<int:post_id>/approve/", approve_post, name="post_approve"),
    path("posts/<int:post_id>/reject/", reject_post, name="post_reject"),
    path("posts/<int:post_id>/report/", report_post, name="post_report"),

    path("users/<int:user_id>/censorship/", set_user_censorship, name="set_user_censorship"),

    path("staff/notify/", admin_notify_page, name="admin_notify"),
    path("staff/notify/api/", admin_notify_api, name="admin_notify_api"),
    path("staff/notify/user-suggest/", admin_user_suggest, name="admin_user_suggest"),

    path("help/request/", help_request_view, name="help_request"),
    path("staff/help-requests/", staff_help_requests_page, name="staff_help_requests"),
    path("staff/help-requests/data/", staff_help_requests_data, name="staff_help_requests_data"),
    path("staff/help-requests/api/", staff_help_requests_api, name="staff_help_requests_api"),

    path("my-wellness/", my_wellness_view, name="my_wellness"),
    path("api/wellness/entries/", wellness_entries_api, name="wellness_entries_api"),
    path("api/wellness/settings/", wellness_settings_api, name="wellness_settings_api"),
    path("patients/<int:user_id>/wellness/", patient_wellness_view, name="patient_wellness"),

    path("banned/", banned_view, name="banned"),
    path("staff/users/<int:user_id>/ban/", toggle_user_ban, name="toggle_user_ban"),

    path("my-health/", my_health_view, name="my_health"),
    path("my-health/", my_health_view, name="my_health"),
    path("my-health/partials/documents/", health_documents_partial, name="health_documents_partial"),
    path("my-health/partials/recommendations/", health_recommendations_partial, name="health_recommendations_partial"),
    path("my-health/partials/wellness/", health_wellness_partial, name="health_wellness_partial"),

    path("set-language/", set_language, name="set_language"),
]
