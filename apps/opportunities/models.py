from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Opportunity(models.Model):
    class Category(models.TextChoices):
        INTERNSHIP = "internship", "Internship"
        JOB = "job", "Job"
        HACKATHON = "hackathon", "Hackathon"
        SCHOLARSHIP = "scholarship", "Scholarship"
        WORKSHOP = "workshop", "Workshop"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        SAVED = "saved", "Saved"
        APPLIED = "applied", "Applied"
        EXPIRED = "expired", "Expired"

    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name="opportunities")
    company = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    eligibility = models.CharField(max_length=255, blank=True)
    deadline = models.DateField(null=True, blank=True)
    application_link = models.URLField(blank=True)
    category = models.CharField(max_length=32, choices=Category.choices, default=Category.OTHER)
    description = models.TextField(blank=True)
    summary = models.TextField(blank=True, default="", db_default="")
    created_at = models.DateTimeField(auto_now_add=True)
    is_saved = models.BooleanField(default=False)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.SAVED)
    duplicate_count = models.PositiveIntegerField(default=0, db_default=0)

    class Meta:
        ordering = ["deadline", "-created_at"]
        indexes = [
            models.Index(fields=["owner"]),
            models.Index(fields=["company"]),
            models.Index(fields=["deadline"]),
            models.Index(fields=["category"]),
            models.Index(fields=["owner", "company", "role", "deadline"]),
        ]

    def __str__(self):
        return f"{self.company} - {self.role}"

    @property
    def days_until_deadline(self):
        if not self.deadline:
            return None
        return (self.deadline - timezone.localdate()).days

    @property
    def deadline_state(self):
        days_left = self.days_until_deadline
        if days_left is None:
            return "unknown"
        if days_left < 0:
            return "expired"
        if days_left < 3:
            return "urgent"
        if days_left <= 7:
            return "warning"
        return "safe"


class OpportunityNote(models.Model):
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="notes")
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="opportunity_notes")
    content = models.CharField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note for {self.opportunity_id}: {self.content[:40]}"


class NotificationLog(models.Model):
    class TriggerType(models.TextChoices):
        IMMEDIATE = "immediate", "Immediate"
        WEEK_BEFORE = "week_before", "Week Before"
        THREE_DAYS = "three_days", "Three Days Before"
        ONE_DAY = "one_day", "One Day Before"

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        PUSH = "push", "Push"

    class Status(models.TextChoices):
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="notification_logs")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notification_logs")
    trigger_type = models.CharField(max_length=32, choices=TriggerType.choices)
    channel = models.CharField(max_length=16, choices=Channel.choices)
    status = models.CharField(max_length=16, choices=Status.choices)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "trigger_type", "channel"]),
            models.Index(fields=["opportunity", "trigger_type", "channel"]),
        ]

    def __str__(self):
        return f"{self.user_id} {self.trigger_type} {self.channel} {self.status}"
