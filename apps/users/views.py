from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.urls import reverse
from django.shortcuts import redirect, render
from urllib.parse import quote
import uuid

from .forms import SignInForm, SignUpForm, UserProfileForm
from .models import UserProfile


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.email = form.cleaned_data["email"]
            user.save(update_fields=["email"])
            login(request, user)
            messages.success(request, "Account created successfully.")
            return redirect("dashboard")
    else:
        form = SignUpForm()

    return render(request, "users/signup.html", {"form": form})


def signin_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = SignInForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, "Signed in successfully.")
            return redirect("dashboard")
    else:
        form = SignInForm()

    return render(request, "users/signin.html", {"form": form})


def signout_view(request):
    if request.method == "POST":
        logout(request)
        messages.info(request, "Signed out.")
    return redirect("signin")


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        if "regen_calendar_token" in request.POST:
            profile.calendar_token = str(uuid.uuid4())
            profile.save(update_fields=["calendar_token"])
            messages.success(request, "Calendar feed link regenerated. Re-subscribe once in Google Calendar.")
            return redirect("profile")
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("profile")
    else:
        form = UserProfileForm(instance=profile)

    feed_path = reverse("calendar_feed", kwargs={"token": profile.calendar_token})
    http_feed = f"{settings.APP_BASE_URL}{feed_path}"
    webcal_feed = http_feed.replace("https://", "webcal://").replace("http://", "webcal://")
    google_subscribe = f"https://calendar.google.com/calendar/u/0/r/settings/addbyurl?cid={quote(http_feed, safe='')}"

    return render(
        request,
        "users/profile.html",
        {
            "form": form,
            "calendar_feed_http": http_feed,
            "calendar_feed_webcal": webcal_feed,
            "calendar_google_subscribe": google_subscribe,
        },
    )
