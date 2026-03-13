from django.contrib.auth.models import User
from django.db import models
import uuid


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=120, blank=True)
    college = models.CharField(max_length=180, blank=True)
    degree = models.CharField(max_length=120, blank=True)
    graduation_year = models.PositiveIntegerField(null=True, blank=True)
    skills = models.TextField(blank=True)
    bio = models.TextField(blank=True)
    calendar_token = models.CharField(max_length=64, unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.full_name or self.user.username


class DeviceToken(models.Model):
    class Platform(models.TextChoices):
        ANDROID = "android", "Android"
        IOS = "ios", "iOS"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="device_tokens")
    token = models.CharField(max_length=255)
    platform = models.CharField(max_length=20, choices=Platform.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "token")

    def __str__(self):
        return f"{self.user.username} - {self.platform}"
