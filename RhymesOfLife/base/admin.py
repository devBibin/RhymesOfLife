from django.contrib import admin, messages
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.admin.widgets import AdminTextareaWidget

from .models import (
    AdditionalUserInfo,
    MedicalDocument,
    MedicalExam,
    Notification,
    Follower,
    ExamComment,
    PhoneVerification,
    TelegramAccount,
    Config,
    HelpRequest,
    WellnessEntry,
    WellnessSettings,
    PasswordResetCode,
    Recommendation,
    Post, PostImage, PostLike, PostComment, PostReport,
    PatientAccessRequest,
)


class SoftDeleteAdminMixin:
    actions = ("action_soft_delete", "action_restore", "action_hard_delete")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        manager = getattr(self.model, "all_objects", None)
        return manager.all() if manager else qs

    @admin.action(description=_("Soft delete selected"))
    def action_soft_delete(self, request, queryset):
        updated = 0
        for obj in queryset:
            if getattr(obj, "is_deleted", False) is False:
                obj.is_deleted = True
                obj.deleted_at = timezone.now()
                obj.save(update_fields=["is_deleted", "deleted_at"])
                updated += 1
        self.message_user(request, _("%(n)d objects soft-deleted.") % {"n": updated}, messages.SUCCESS)

    @admin.action(description=_("Restore selected"))
    def action_restore(self, request, queryset):
        updated = queryset.update(is_deleted=False, deleted_at=None)
        self.message_user(request, _("%(n)d objects restored.") % {"n": updated}, messages.SUCCESS)

    @admin.action(description=_("Hard delete selected"))
    def action_hard_delete(self, request, queryset):
        deleted = 0
        for obj in queryset:
            if hasattr(obj, "hard_delete"):
                obj.hard_delete()
            else:
                obj.delete()
            deleted += 1
        self.message_user(request, _("%(n)d objects permanently deleted.") % {"n": deleted}, messages.WARNING)


class IsDeletedListFilter(admin.SimpleListFilter):
    title = _("Deleted")
    parameter_name = "is_deleted"

    def lookups(self, request, model_admin):
        return (("1", _("Yes")), ("0", _("No")),)

    def queryset(self, request, queryset):
        val = self.value()
        if val == "1":
            return queryset.filter(is_deleted=True)
        if val == "0":
            return queryset.filter(is_deleted=False)
        return queryset


class JSONFieldAdminMixin:
    formfield_overrides = {
        models.JSONField: {"widget": AdminTextareaWidget(attrs={"rows": 8, "cols": 80})},
    }


@admin.register(Config)
class ConfigAdmin(JSONFieldAdminMixin, admin.ModelAdmin):
    list_display = ("key", "updated_at")
    search_fields = ("key",)
    readonly_fields = ("updated_at",)
    list_per_page = 50


@admin.register(AdditionalUserInfo)
class AdditionalUserInfoAdmin(admin.ModelAdmin):
    list_display = ("user", "language", "is_verified", "email_verified", "phone_verified", "followers_count")
    list_filter = ("language", "is_verified", "email_verified", "phone_verified")
    search_fields = ("user__username", "email", "first_name", "last_name", "phone")
    raw_id_fields = ("user",)
    readonly_fields = ("followers_count",)
    list_select_related = ("user",)
    list_per_page = 50


class MedicalDocumentInline(admin.TabularInline):
    model = MedicalDocument
    extra = 0
    raw_id_fields = ("exam",)


class ExamCommentInline(admin.TabularInline):
    model = ExamComment
    extra = 0
    raw_id_fields = ("author",)


@admin.register(MedicalExam)
class MedicalExamAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("id", "user_info", "exam_date", "created_at", "is_deleted")
    list_filter = ("exam_date", IsDeletedListFilter)
    date_hierarchy = "exam_date"
    search_fields = ("user_info__user__username",)
    raw_id_fields = ("user_info",)
    inlines = (MedicalDocumentInline, ExamCommentInline)
    list_select_related = ("user_info__user",)
    list_per_page = 50


@admin.register(MedicalDocument)
class MedicalDocumentAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("id", "exam", "file", "external_url", "uploaded_at", "is_deleted")
    search_fields = ("file", "external_url", "exam__user_info__user__username")
    list_filter = (IsDeletedListFilter,)
    raw_id_fields = ("exam",)
    date_hierarchy = "uploaded_at"
    list_per_page = 50


class IsReadFilter(admin.SimpleListFilter):
    title = _("Read")
    parameter_name = "is_read"

    def lookups(self, request, model_admin):
        return (("1", _("Yes")), ("0", _("No")),)

    def queryset(self, request, queryset):
        val = self.value()
        if val == "1":
            return queryset.filter(is_read=True)
        if val == "0":
            return queryset.filter(is_read=False)
        return queryset


@admin.register(Notification)
class NotificationAdmin(SoftDeleteAdminMixin, JSONFieldAdminMixin, admin.ModelAdmin):
    actions = SoftDeleteAdminMixin.actions + ("mark_as_read", "mark_as_unread")
    list_display = ("id", "notification_type", "recipient", "source", "scope", "is_read", "created_at", "is_deleted")
    list_filter = ("notification_type", "source", "scope", IsReadFilter, IsDeletedListFilter, "created_at")
    search_fields = ("title", "message", "recipient__user__username", "sender__user__username")
    raw_id_fields = ("recipient", "sender")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    list_select_related = ("recipient__user", "sender__user")
    list_per_page = 50

    @admin.action(description=_("Mark as read"))
    def mark_as_read(self, request, queryset):
        n = queryset.update(is_read=True)
        self.message_user(request, _("%(n)d notifications marked as read.") % {"n": n}, messages.SUCCESS)

    @admin.action(description=_("Mark as unread"))
    def mark_as_unread(self, request, queryset):
        n = queryset.update(is_read=False)
        self.message_user(request, _("%(n)d notifications marked as unread.") % {"n": n}, messages.SUCCESS)


@admin.register(Follower)
class FollowerAdmin(admin.ModelAdmin):
    list_display = ("id", "follower", "following", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("follower__user__username", "following__user__username")
    raw_id_fields = ("follower", "following")
    date_hierarchy = "created_at"
    list_select_related = ("follower__user", "following__user")
    list_per_page = 50


@admin.register(ExamComment)
class ExamCommentAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("id", "exam", "author", "created_at", "is_deleted")
    list_filter = (IsDeletedListFilter, "created_at")
    search_fields = ("author__user__username", "exam__user_info__user__username", "content")
    raw_id_fields = ("exam", "author")
    date_hierarchy = "created_at"
    list_select_related = ("author__user", "exam__user_info__user")
    list_per_page = 50


@admin.register(PhoneVerification)
class PhoneVerificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user_info", "phone", "status", "created_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("user_info__user__username", "phone", "provider_session_id")
    raw_id_fields = ("user_info",)
    date_hierarchy = "created_at"
    list_select_related = ("user_info__user",)
    list_per_page = 50


@admin.register(TelegramAccount)
class TelegramAccountAdmin(admin.ModelAdmin):
    list_display = ("id", "user_info", "telegram_id", "username", "telegram_verified", "created_at")
    list_filter = ("telegram_verified", "created_at")
    search_fields = ("telegram_id", "username", "user_info__user__username")
    raw_id_fields = ("user_info",)
    date_hierarchy = "created_at"
    list_select_related = ("user_info__user",)
    list_per_page = 50


@admin.register(PasswordResetCode)
class PasswordResetCodeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "channel", "code", "token", "expires_at", "attempts_left", "used_at", "created_at")
    list_filter = ("channel", "created_at", "expires_at")
    search_fields = ("user__username", "code", "token")
    raw_id_fields = ("user",)
    date_hierarchy = "created_at"
    list_select_related = ("user",)
    list_per_page = 50


@admin.register(HelpRequest)
class HelpRequestAdmin(admin.ModelAdmin):
    actions = ("mark_processed", "mark_unprocessed")
    list_display = ("__str__", "email", "phone", "city", "status", "processed_by", "created_at", "processed_at")
    list_filter = ("status", "is_processed", "created_at", "processed_at")
    search_fields = ("email", "name", "phone", "city", "syndrome", "gen", "medications", "message", "user__username")
    readonly_fields = ("created_at", "processed_at", "processed_by")
    date_hierarchy = "created_at"
    list_select_related = ("processed_by", "user")
    list_per_page = 50

    @admin.action(description=_("Mark as processed"))
    def mark_processed(self, request, queryset):
        n = 0
        for obj in queryset:
            obj.mark_processed(request.user)
            n += 1
        self.message_user(request, _("%(n)d requests processed.") % {"n": n}, messages.SUCCESS)

    @admin.action(description=_("Mark as unprocessed"))
    def mark_unprocessed(self, request, queryset):
        n = 0
        for obj in queryset:
            obj.mark_unprocessed()
            n += 1
        self.message_user(request, _("%(n)d requests reverted to unprocessed.") % {"n": n}, messages.SUCCESS)


@admin.register(WellnessSettings)
class WellnessSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "user_info", "tg_notifications_enabled", "email_notifications_enabled",
        "reminder_hour", "reminder_minute", "reminder_interval", "updated_at",
    )
    list_filter = ("tg_notifications_enabled", "email_notifications_enabled", "reminder_interval")
    search_fields = ("user_info__user__username",)
    raw_id_fields = ("user_info",)
    list_select_related = ("user_info__user",)
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 50


@admin.register(WellnessEntry)
class WellnessEntryAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("user_info", "date", "score", "created_at", "is_deleted")
    list_filter = ("date", IsDeletedListFilter, "score")
    search_fields = ("user_info__user__username", "note")
    raw_id_fields = ("user_info",)
    date_hierarchy = "date"
    list_select_related = ("user_info__user",)
    list_per_page = 50


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 0


class PostCommentInline(admin.TabularInline):
    model = PostComment
    extra = 0
    raw_id_fields = ("author",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    actions = ("approve_selected", "hide_selected", "unhide_selected")
    list_display = (
        "id", "author", "is_approved", "is_hidden", "is_deleted",
        "likes_count", "comments_count", "reports_count", "created_at",
    )
    list_filter = ("is_approved", "is_hidden", "is_deleted", "created_at")
    search_fields = ("author__user__username", "text")
    raw_id_fields = ("author", "approved_by")
    date_hierarchy = "created_at"
    inlines = (PostImageInline, PostCommentInline)
    list_select_related = ("author__user", "approved_by")
    list_per_page = 50

    @admin.action(description=_("Approve selected"))
    def approve_selected(self, request, queryset):
        n = queryset.filter(is_approved=False).update(
            is_approved=True, approved_at=timezone.now(), approved_by=request.user
        )
        self.message_user(request, _("%(n)d posts approved.") % {"n": n}, messages.SUCCESS)

    @admin.action(description=_("Hide selected"))
    def hide_selected(self, request, queryset):
        n = queryset.filter(is_hidden=False).update(is_hidden=True)
        self.message_user(request, _("%(n)d posts hidden.") % {"n": n}, messages.SUCCESS)

    @admin.action(description=_("Unhide selected"))
    def unhide_selected(self, request, queryset):
        n = queryset.filter(is_hidden=True).update(is_hidden=False)
        self.message_user(request, _("%(n)d posts unhidden.") % {"n": n}, messages.SUCCESS)


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "author", "is_deleted", "created_at", "edited_at")
    list_filter = ("is_deleted", "created_at")
    search_fields = ("post__id", "author__user__username", "text")
    raw_id_fields = ("post", "author")
    date_hierarchy = "created_at"
    list_select_related = ("post", "author__user")
    list_per_page = 50


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "author", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("post__id", "author__user__username")
    raw_id_fields = ("post", "author")
    date_hierarchy = "created_at"
    list_select_related = ("post", "author__user")
    list_per_page = 50


@admin.register(PostReport)
class PostReportAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "author", "created_at")
    list_filter = ("created_at",)
    search_fields = ("post__id", "author__user__username")
    raw_id_fields = ("post", "author")
    date_hierarchy = "created_at"
    list_select_related = ("post", "author__user")
    list_per_page = 50


@admin.register(Recommendation)
class RecommendationAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("id", "patient", "author", "created_at", "is_deleted")
    list_filter = (IsDeletedListFilter, "created_at")
    search_fields = ("patient__user__username", "author__user__username", "content")
    raw_id_fields = ("patient", "author")
    date_hierarchy = "created_at"
    list_select_related = ("patient__user", "author__user")
    list_per_page = 50


@admin.register(PatientAccessRequest)
class PatientAccessRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "doctor", "patient", "status", "created_at", "decided_at")
    list_filter = ("status", "created_at", "decided_at")
    search_fields = ("doctor__user__username", "patient__user__username")
    raw_id_fields = ("doctor", "patient")
    date_hierarchy = "created_at"
    list_select_related = ("doctor__user", "patient__user")
    list_per_page = 50
