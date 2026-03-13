from datetime import datetime, time, timedelta
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import OpportunityForm, OpportunityNoteForm
from .models import Opportunity
from apps.users.models import UserProfile


def _owned_opportunity_or_404(user, pk):
    return get_object_or_404(Opportunity, pk=pk, owner=user)


def _escape_ics_text(value):
    if not value:
        return ""
    return str(value).replace("\\", "\\\\").replace(";", r"\;").replace(",", r"\,").replace("\n", r"\n")


def _ics_datetime(dt):
    return dt.strftime("%Y%m%dT%H%M%S")


def _build_ics_event(opportunity, now):
    start_dt = datetime.combine(opportunity.deadline, time(hour=9, minute=0))
    end_dt = start_dt + timedelta(hours=1)

    uid = f"opportunityhub-{opportunity.id}@local"
    summary = _escape_ics_text(f"{opportunity.company} - {opportunity.role}")
    description = _escape_ics_text(
        f"Category: {opportunity.get_category_display()}\n"
        f"Eligibility: {opportunity.eligibility or 'Not specified'}\n"
        f"Apply: {opportunity.application_link or 'Not specified'}\n"
        f"Notes: {opportunity.summary or opportunity.description or ''}"
    )

    alarms = [
        "BEGIN:VALARM\nACTION:DISPLAY\nDESCRIPTION:Opportunity reminder (7 days)\nTRIGGER:-P7D\nEND:VALARM",
        "BEGIN:VALARM\nACTION:DISPLAY\nDESCRIPTION:Opportunity reminder (3 days)\nTRIGGER:-P3D\nEND:VALARM",
        "BEGIN:VALARM\nACTION:DISPLAY\nDESCRIPTION:Opportunity reminder (1 day)\nTRIGGER:-P1D\nEND:VALARM",
    ]

    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{_ics_datetime(now)}Z",
        f"DTSTART:{_ics_datetime(start_dt)}",
        f"DTEND:{_ics_datetime(end_dt)}",
        f"SUMMARY:{summary}",
        f"DESCRIPTION:{description}",
        *alarms,
        "END:VEVENT",
    ]
    return "\r\n".join(lines)


def _build_ics_calendar(events_text):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//OpportunityHub//Reminder Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:OpportunityHub Deadlines",
        "X-WR-TIMEZONE:UTC",
        "REFRESH-INTERVAL;VALUE=DURATION:PT1H",
        "X-PUBLISHED-TTL:PT1H",
        *events_text,
        "END:VCALENDAR",
    ]
    return "\r\n".join(lines) + "\r\n"


def _build_google_calendar_url(opportunity):
    if not opportunity.deadline:
        return ""
    start_date = opportunity.deadline.strftime("%Y%m%d")
    end_date = (opportunity.deadline + timedelta(days=1)).strftime("%Y%m%d")
    text = f"{opportunity.company} - {opportunity.role}"
    details = (
        f"Category: {opportunity.get_category_display()}\n"
        f"Eligibility: {opportunity.eligibility or 'Not specified'}\n"
        f"Apply: {opportunity.application_link or 'Not specified'}\n"
        f"Summary: {opportunity.summary or opportunity.description or ''}"
    )
    params = urlencode(
        {
            "action": "TEMPLATE",
            "text": text,
            "dates": f"{start_date}/{end_date}",
            "details": details,
        }
    )
    return f"https://calendar.google.com/calendar/render?{params}"


@login_required
def opportunity_detail(request, pk):
    opportunity = _owned_opportunity_or_404(request.user, pk)
    note_form = OpportunityNoteForm()
    google_calendar_link = _build_google_calendar_url(opportunity)
    open_calendar = request.GET.get("open_calendar") == "1" and bool(google_calendar_link)
    return render(
        request,
        "opportunities/opportunity_detail.html",
        {
            "opportunity": opportunity,
            "note_form": note_form,
            "google_calendar_link": google_calendar_link,
            "open_calendar": open_calendar,
        },
    )


@login_required
def export_calendar_event(request, pk):
    opportunity = _owned_opportunity_or_404(request.user, pk)
    if not opportunity.deadline:
        messages.warning(request, "Calendar export requires a valid deadline.")
        return redirect("opportunity_detail", pk=opportunity.pk)

    now_utc = timezone.now().replace(tzinfo=None)
    event_text = _build_ics_event(opportunity, now_utc)
    ics_content = _build_ics_calendar([event_text])
    filename = f"opportunity_{opportunity.id}.ics"

    response = HttpResponse(ics_content, content_type="text/calendar; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def calendar_feed(request, token):
    profile = UserProfile.objects.filter(calendar_token=token).order_by("id").first()
    if not profile:
        return HttpResponse("Calendar feed not found.", status=404)
    opportunities = (
        Opportunity.objects.filter(owner=profile.user, deadline__isnull=False, status=Opportunity.Status.SAVED)
        .order_by("deadline")
    )
    now_utc = timezone.now().replace(tzinfo=None)
    events = [_build_ics_event(opportunity, now_utc) for opportunity in opportunities]
    ics_content = _build_ics_calendar(events)
    response = HttpResponse(ics_content, content_type="text/calendar; charset=utf-8")
    response["Content-Disposition"] = 'inline; filename="opportunityhub_feed.ics"'
    response["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    response["Last-Modified"] = timezone.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
    return response


@login_required
def add_note(request, pk):
    opportunity = _owned_opportunity_or_404(request.user, pk)
    if request.method == "POST":
        form = OpportunityNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.opportunity = opportunity
            note.created_by = request.user
            note.save()
            messages.success(request, "Personal note added.")
    return redirect("opportunity_detail", pk=opportunity.pk)


@login_required
def saved_opportunities(request):
    opportunities = Opportunity.objects.filter(owner=request.user, is_saved=True)
    return render(
        request,
        "opportunities/saved_opportunities.html",
        {"opportunities": opportunities},
    )


@login_required
def toggle_saved(request, pk):
    opportunity = _owned_opportunity_or_404(request.user, pk)
    opportunity.is_saved = not opportunity.is_saved
    opportunity.save(update_fields=["is_saved"])
    return redirect(request.META.get("HTTP_REFERER", "dashboard"))


@login_required
def opportunity_create(request):
    if request.method == "POST":
        form = OpportunityForm(request.POST)
        if form.is_valid():
            opportunity = form.save(commit=False)
            opportunity.owner = request.user
            opportunity.save()
            messages.success(request, "Opportunity created.")
            return redirect("opportunity_detail", pk=opportunity.pk)
    else:
        form = OpportunityForm()

    return render(
        request,
        "opportunities/opportunity_form.html",
        {"form": form, "page_title": "Create Opportunity"},
    )


@login_required
def opportunity_update(request, pk):
    opportunity = _owned_opportunity_or_404(request.user, pk)
    if request.method == "POST":
        form = OpportunityForm(request.POST, instance=opportunity)
        if form.is_valid():
            form.save()
            messages.success(request, "Opportunity updated.")
            return redirect("opportunity_detail", pk=opportunity.pk)
    else:
        form = OpportunityForm(instance=opportunity)

    return render(
        request,
        "opportunities/opportunity_form.html",
        {"form": form, "page_title": "Edit Opportunity", "opportunity": opportunity},
    )


@login_required
def opportunity_delete(request, pk):
    opportunity = _owned_opportunity_or_404(request.user, pk)
    if request.method == "POST":
        opportunity.delete()
        messages.success(request, "Opportunity deleted.")
        return redirect("dashboard")

    return render(
        request,
        "opportunities/opportunity_confirm_delete.html",
        {"opportunity": opportunity},
    )
