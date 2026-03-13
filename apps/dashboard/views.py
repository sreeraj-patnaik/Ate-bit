from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

from apps.opportunities.models import Opportunity


def home(request):
    if request.user.is_authenticated:
        scoped = Opportunity.objects.filter(owner=request.user)
        latest_opportunities = scoped.order_by("-created_at")[:3]
        context = {
            "latest_opportunities": latest_opportunities,
            "total_count": scoped.count(),
            "saved_count": scoped.filter(is_saved=True).count(),
            "applied_count": scoped.filter(status=Opportunity.Status.APPLIED).count(),
            "upcoming_count": scoped.filter(deadline__gte=timezone.localdate()).count(),
        }
    else:
        latest_opportunities = Opportunity.objects.order_by("-created_at")[:3]
        context = {
            "latest_opportunities": latest_opportunities,
            "total_count": Opportunity.objects.count(),
            "saved_count": 0,
            "applied_count": 0,
            "upcoming_count": 0,
        }
    return render(request, "dashboard/home.html", context)


@login_required
def dashboard(request):
    opportunities = Opportunity.objects.filter(owner=request.user)
    search_query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "all")
    status = request.GET.get("status", "all")
    saved_only = request.GET.get("saved", "0") == "1"
    deadline_from = request.GET.get("from", "").strip()
    deadline_to = request.GET.get("to", "").strip()
    sort = request.GET.get("sort", "deadline_asc")

    if search_query:
        opportunities = opportunities.filter(
            Q(company__icontains=search_query)
            | Q(role__icontains=search_query)
            | Q(summary__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(eligibility__icontains=search_query)
        )

    if category != "all":
        opportunities = opportunities.filter(category=category)

    if status != "all":
        opportunities = opportunities.filter(status=status)

    if saved_only:
        opportunities = opportunities.filter(is_saved=True)

    if deadline_from:
        opportunities = opportunities.filter(deadline__gte=deadline_from)

    if deadline_to:
        opportunities = opportunities.filter(deadline__lte=deadline_to)

    sort_map = {
        "deadline_asc": ["deadline", "-created_at"],
        "deadline_desc": ["-deadline", "-created_at"],
        "newest": ["-created_at"],
        "company": ["company", "role"],
    }
    opportunities = opportunities.order_by(*sort_map.get(sort, sort_map["deadline_asc"]))

    context = {
        "opportunities": opportunities,
        "search_query": search_query,
        "selected_category": category,
        "selected_status": status,
        "category_choices": Opportunity.Category.choices,
        "status_choices": Opportunity.Status.choices,
        "saved_only": saved_only,
        "deadline_from": deadline_from,
        "deadline_to": deadline_to,
        "sort": sort,
    }
    return render(request, "dashboard/dashboard.html", context)


@login_required
def timeline(request):
    start = timezone.localdate()
    end = start + timedelta(days=60)
    upcoming = (
        Opportunity.objects.filter(owner=request.user, deadline__gte=start, deadline__lte=end)
        .exclude(deadline__isnull=True)
        .order_by("deadline", "company")
    )

    grouped = {}
    for item in upcoming:
        grouped.setdefault(item.deadline, []).append(item)

    timeline_items = [{"date": day, "items": items} for day, items in grouped.items()]
    return render(request, "dashboard/timeline.html", {"timeline_items": timeline_items, "range_end": end})
