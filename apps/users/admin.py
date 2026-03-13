from django.contrib import admin

from .models import DeviceToken, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "college", "graduation_year")
    search_fields = ("user__username", "full_name", "college", "degree")


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "platform", "is_active", "updated_at")
    search_fields = ("user__username", "token")
    list_filter = ("platform", "is_active")
