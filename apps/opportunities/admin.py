from django.contrib import admin

from .models import NotificationLog, Opportunity, OpportunityNote


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ("company", "role", "category", "deadline", "status", "is_saved", "duplicate_count")
    list_filter = ("category", "status", "is_saved")
    search_fields = ("company", "role", "summary", "description", "eligibility")


@admin.register(OpportunityNote)
class OpportunityNoteAdmin(admin.ModelAdmin):
    list_display = ("opportunity", "content", "created_at")
    search_fields = ("content",)


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("opportunity", "user", "trigger_type", "channel", "status", "created_at")
    list_filter = ("trigger_type", "channel", "status")
    search_fields = ("user__username", "opportunity__company", "opportunity__role", "details")
