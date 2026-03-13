from datetime import timedelta

from django.utils import timezone

from apps.opportunities.models import NotificationLog, Opportunity


def urgent_deadlines(request):
    if not request.user.is_authenticated:
        return {
            "urgent_opportunities": [],
            "urgent_count": 0,
            "has_urgent_modal": False,
        }

    today = timezone.localdate()
    soon = today + timedelta(days=3)
    opportunities = (
        Opportunity.objects.filter(owner=request.user, deadline__isnull=False, deadline__lte=soon)
        .order_by("deadline")[:6]
    )

    urgent_items = []
    for item in opportunities:
        urgent_items.append(
            {
                "id": item.id,
                "company": item.company,
                "role": item.role,
                "deadline": item.deadline,
                "days_left": item.days_until_deadline,
            }
        )

    followup_items = []
    email_logs = (
        NotificationLog.objects.select_related("opportunity")
        .filter(
            user=request.user,
            channel=NotificationLog.Channel.EMAIL,
            status=NotificationLog.Status.SENT,
        )
        .order_by("-created_at")
    )
    latest_by_opportunity = {}
    for log in email_logs:
        if log.opportunity_id not in latest_by_opportunity:
            latest_by_opportunity[log.opportunity_id] = log

    for log in latest_by_opportunity.values():
        opp = log.opportunity
        if not opp:
            continue
        if opp.status != Opportunity.Status.SAVED:
            continue
        followup_items.append(
            {
                "id": opp.id,
                "company": opp.company,
                "role": opp.role,
                "last_email_at": log.created_at,
            }
        )

    path = request.path or ""
    show_on_home = path == "/"

    return {
        "urgent_opportunities": urgent_items,
        "urgent_count": len(urgent_items),
        "email_followup_opportunities": followup_items[:6],
        "email_followup_count": len(followup_items),
        "has_urgent_modal": show_on_home and (len(urgent_items) > 0 or len(followup_items) > 0),
    }
