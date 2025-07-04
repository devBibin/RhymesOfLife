from django.contrib import admin
from .models import *

@admin.register(AdditionalUserInfo)
class AdditionalUserInfoAdmin(admin.ModelAdmin):
    search_fields = ("user__username", )
    raw_id_fields = ["user", ]
