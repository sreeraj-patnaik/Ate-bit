from django.contrib.auth.models import User
from rest_framework import serializers

from apps.opportunities.models import Opportunity, OpportunityNote
from apps.users.models import DeviceToken, UserProfile


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["full_name", "college", "degree", "graduation_year", "skills", "bio"]


class OpportunityNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpportunityNote
        fields = ["id", "content", "created_at"]
        read_only_fields = ["id", "created_at"]


class OpportunitySerializer(serializers.ModelSerializer):
    notes = OpportunityNoteSerializer(many=True, read_only=True)

    class Meta:
        model = Opportunity
        fields = [
            "id",
            "company",
            "role",
            "eligibility",
            "deadline",
            "application_link",
            "category",
            "summary",
            "description",
            "is_saved",
            "status",
            "duplicate_count",
            "created_at",
            "notes",
        ]
        read_only_fields = ["id", "duplicate_count", "created_at", "notes"]


class ExtractMessageSerializer(serializers.Serializer):
    message_text = serializers.CharField()


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ["token", "platform", "is_active"]
