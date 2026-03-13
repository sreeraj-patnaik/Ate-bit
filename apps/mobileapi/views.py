from datetime import timedelta

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, response, status, views

from apps.opportunities.models import Opportunity, OpportunityNote
from apps.users.models import UserProfile
from services.notification_service import send_immediate_notifications
from services.opportunity_parser import OpportunityParser

from .serializers import (
    DeviceTokenSerializer,
    ExtractMessageSerializer,
    OpportunityNoteSerializer,
    OpportunitySerializer,
    RegisterSerializer,
    UserProfileSerializer,
)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile)
        return response.Response(serializer.data)

    def put(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data)


class OpportunityListCreateView(generics.ListCreateAPIView):
    serializer_class = OpportunitySerializer

    def get_queryset(self):
        queryset = Opportunity.objects.filter(owner=self.request.user)
        query = self.request.query_params.get("q", "").strip()
        if query:
            queryset = queryset.filter(company__icontains=query)
        return queryset.order_by("deadline", "-created_at")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class OpportunityDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OpportunitySerializer

    def get_queryset(self):
        return Opportunity.objects.filter(owner=self.request.user)


class ExtractOpportunityView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ExtractMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        parser = OpportunityParser()
        opportunity = parser.create_opportunity_from_message(
            serializer.validated_data["message_text"],
            user=request.user,
        )
        send_immediate_notifications(opportunity)
        return response.Response(OpportunitySerializer(opportunity).data, status=status.HTTP_201_CREATED)


class AddNoteView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        opportunity = get_object_or_404(Opportunity, pk=pk, owner=request.user)
        serializer = OpportunityNoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = OpportunityNote.objects.create(
            opportunity=opportunity,
            created_by=request.user,
            content=serializer.validated_data["content"],
        )
        return response.Response(OpportunityNoteSerializer(note).data, status=status.HTTP_201_CREATED)


class TimelineView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        start = timezone.localdate()
        end = start + timedelta(days=60)
        opportunities = (
            Opportunity.objects.filter(owner=request.user, deadline__gte=start, deadline__lte=end)
            .exclude(deadline__isnull=True)
            .order_by("deadline", "company")
        )
        serializer = OpportunitySerializer(opportunities, many=True)
        return response.Response({"start": start, "end": end, "items": serializer.data})


class DeviceTokenView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DeviceTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_value = serializer.validated_data["token"]
        platform = serializer.validated_data["platform"]
        is_active = serializer.validated_data.get("is_active", True)

        token, _ = request.user.device_tokens.update_or_create(
            token=token_value,
            defaults={"platform": platform, "is_active": is_active},
        )
        return response.Response(DeviceTokenSerializer(token).data)
