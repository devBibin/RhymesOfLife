from django.contrib import admin
from .models import *


@admin.register(AdditionalUserInfo)
class AdditionalUserInfoAdmin(admin.ModelAdmin):
    search_fields = ("user__username",)
    raw_id_fields = ["user",]
    list_display = ('user',)


@admin.register(MedicalDocument)
class MedicalDocument(admin.ModelAdmin):
    pass


@admin.register(MedicalExam)
class MedicalExam(admin.ModelAdmin):
    pass


@admin.register(Notification)
class Notification(admin.ModelAdmin):
    pass


@admin.register(Follower)
class Follower(admin.ModelAdmin):
    pass


@admin.register(ExamComment)
class ExamComment(admin.ModelAdmin):
    pass


@admin.register(PhoneVerification)
class PhoneVerification(admin.ModelAdmin):
    pass


@admin.register(TelegramAccount)
class TelegramAccount(admin.ModelAdmin):
    pass


@admin.register(Config)
class Config(admin.ModelAdmin):
    pass
