import os
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.mail import send_mail
from django.utils import timezone

from apps.opportunities.models import NotificationLog, Opportunity

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
except ImportError:  # pragma: no cover
    firebase_admin = None
    credentials = None
    messaging = None


def send_immediate_notifications(opportunity):
    _send_for_trigger(opportunity, NotificationLog.TriggerType.IMMEDIATE, allow_repeat=True)


def send_deadline_reminders(reference_date=None):
    today = reference_date or timezone.localdate()
    reminder_map = {
        7: NotificationLog.TriggerType.WEEK_BEFORE,
        3: NotificationLog.TriggerType.THREE_DAYS,
        1: NotificationLog.TriggerType.ONE_DAY,
    }

    results = []
    for delta_days, trigger in reminder_map.items():
        target = today + timedelta(days=delta_days)
        opportunities = Opportunity.objects.filter(deadline=target).exclude(owner__isnull=True)
        for opportunity in opportunities:
            result = _send_for_trigger(opportunity, trigger, allow_repeat=False)
            results.append(result)
    return results


def _send_for_trigger(opportunity, trigger_type, allow_repeat=False):
    user = opportunity.owner
    if not user:
        return {"sent": 0, "reason": "missing_owner"}

    sent_count = 0

    if user.email and (allow_repeat or not _already_sent(opportunity, user, trigger_type, NotificationLog.Channel.EMAIL)):
        subject, body_text, body_html = _build_message(opportunity, trigger_type)
        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=body_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email.attach_alternative(body_html, "text/html")
            email.send(fail_silently=False)
            NotificationLog.objects.create(
                opportunity=opportunity,
                user=user,
                trigger_type=trigger_type,
                channel=NotificationLog.Channel.EMAIL,
                status=NotificationLog.Status.SENT,
            )
            sent_count += 1
        except Exception as exc:  # pragma: no cover
            NotificationLog.objects.create(
                opportunity=opportunity,
                user=user,
                trigger_type=trigger_type,
                channel=NotificationLog.Channel.EMAIL,
                status=NotificationLog.Status.FAILED,
                details=str(exc),
            )

    if allow_repeat or not _already_sent(opportunity, user, trigger_type, NotificationLog.Channel.PUSH):
        ok, detail = _send_push(user, opportunity, trigger_type)
        NotificationLog.objects.create(
            opportunity=opportunity,
            user=user,
            trigger_type=trigger_type,
            channel=NotificationLog.Channel.PUSH,
            status=NotificationLog.Status.SENT if ok else NotificationLog.Status.FAILED,
            details=detail,
        )
        if ok:
            sent_count += 1

    return {"sent": sent_count, "opportunity_id": opportunity.id, "trigger": trigger_type}


def _already_sent(opportunity, user, trigger_type, channel):
    return NotificationLog.objects.filter(
        opportunity=opportunity,
        user=user,
        trigger_type=trigger_type,
        channel=channel,
        status=NotificationLog.Status.SENT,
    ).exists()


def _build_message(opportunity, trigger_type):
    trigger_titles = {
        NotificationLog.TriggerType.IMMEDIATE: "New opportunity added",
        NotificationLog.TriggerType.WEEK_BEFORE: "Deadline in 7 days",
        NotificationLog.TriggerType.THREE_DAYS: "Deadline in 3 days",
        NotificationLog.TriggerType.ONE_DAY: "Deadline in 1 day",
    }
    title = trigger_titles.get(trigger_type, "Opportunity update")
    subject = f"OpportunityHub: {title} - {opportunity.company} {opportunity.role}"
    detail_url = f"{settings.APP_BASE_URL}/opportunity/{opportunity.id}"
    urgency_label, urgency_bg, urgency_fg = _deadline_color(opportunity)
    body_text = (
        f"{title}\n\n"
        f"DEADLINE: {opportunity.deadline or 'Not specified'}\n\n"
        f"Company: {opportunity.company}\n"
        f"Role: {opportunity.role}\n"
        f"Category: {opportunity.get_category_display()}\n"
        f"Eligibility: {opportunity.eligibility or 'Not specified'}\n"
        f"Application Link: {opportunity.application_link or 'Not provided'}\n\n"
        f"Open in web: {detail_url}\n"
    )

    body_html = f"""
<html>
  <body style="font-family:Arial,Helvetica,sans-serif;background:#f8fafc;color:#0f172a;padding:20px;">
    <div style="max-width:640px;margin:0 auto;background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;">
      <h2 style="margin:0 0 12px 0;">{title}</h2>
      <p style="margin:0 0 12px 0;color:#475569;">Opportunity details are below.</p>
      <div style="background:#0f172a;color:#ffffff;border-radius:12px;padding:14px 16px;margin:0 0 14px 0;">
        <p style="margin:0;font-size:12px;opacity:0.8;letter-spacing:0.5px;text-transform:uppercase;">Primary Deadline</p>
        <p style="margin:2px 0 0 0;font-size:24px;font-weight:800;">{opportunity.deadline or 'Not specified'}</p>
      </div>
      <div style="display:inline-block;background:{urgency_bg};color:{urgency_fg};padding:6px 10px;border-radius:999px;font-size:12px;font-weight:700;margin-bottom:14px;">
        Deadline Status: {urgency_label}
      </div>
      <table style="width:100%;border-collapse:collapse;margin-bottom:14px;">
        <tr><td style="padding:8px;border-bottom:1px solid #e2e8f0;font-weight:700;">Company</td><td style="padding:8px;border-bottom:1px solid #e2e8f0;">{opportunity.company}</td></tr>
        <tr><td style="padding:8px;border-bottom:1px solid #e2e8f0;font-weight:700;">Role</td><td style="padding:8px;border-bottom:1px solid #e2e8f0;">{opportunity.role}</td></tr>
        <tr><td style="padding:8px;border-bottom:1px solid #e2e8f0;font-weight:700;">Category</td><td style="padding:8px;border-bottom:1px solid #e2e8f0;">{opportunity.get_category_display()}</td></tr>
        <tr><td style="padding:8px;border-bottom:1px solid #e2e8f0;font-weight:700;">Deadline</td><td style="padding:8px;border-bottom:1px solid #e2e8f0;">{opportunity.deadline or 'Not specified'}</td></tr>
        <tr><td style="padding:8px;border-bottom:1px solid #e2e8f0;font-weight:700;">Eligibility</td><td style="padding:8px;border-bottom:1px solid #e2e8f0;">{opportunity.eligibility or 'Not specified'}</td></tr>
        <tr><td style="padding:8px;border-bottom:1px solid #e2e8f0;font-weight:700;">Apply Link</td><td style="padding:8px;border-bottom:1px solid #e2e8f0;">{opportunity.application_link or 'Not provided'}</td></tr>
      </table>
      <a href="{detail_url}" style="display:inline-block;background:#2563eb;color:#fff;text-decoration:none;padding:10px 14px;border-radius:8px;font-weight:700;">Open Opportunity</a>
    </div>
  </body>
</html>
"""
    return subject, body_text, body_html


def _deadline_color(opportunity):
    days = opportunity.days_until_deadline
    if days is None:
        return "No deadline", "#e2e8f0", "#334155"
    if days < 0:
        return "Expired", "#fee2e2", "#b91c1c"
    if days < 3:
        return "Urgent (<3 days)", "#fee2e2", "#b91c1c"
    if days <= 7:
        return "Near (3-7 days)", "#fef9c3", "#a16207"
    return "Healthy (>7 days)", "#dcfce7", "#166534"




def _send_push(user, opportunity, trigger_type):
    tokens = list(user.device_tokens.filter(is_active=True).values_list("token", flat=True))
    if not tokens:
        return False, "No active device token"

    if not _init_firebase():
        return False, "Firebase not configured"

    trigger_labels = {
        NotificationLog.TriggerType.IMMEDIATE: "New opportunity parsed",
        NotificationLog.TriggerType.WEEK_BEFORE: "Deadline in 7 days",
        NotificationLog.TriggerType.THREE_DAYS: "Deadline in 3 days",
        NotificationLog.TriggerType.ONE_DAY: "Deadline in 1 day",
    }

    title = trigger_labels.get(trigger_type, "Opportunity alert")
    body = f"{opportunity.company} - {opportunity.role}"

    success = 0
    failures = 0
    for token in tokens:
        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data={
                    "opportunity_id": str(opportunity.id),
                    "trigger_type": trigger_type,
                },
                token=token,
            )
            messaging.send(message)
            success += 1
        except Exception:
            failures += 1

    if success > 0:
        return True, f"Push sent to {success} device(s), failed {failures}"
    return False, f"Push failed for all devices ({failures})"


def _init_firebase():
    if firebase_admin is None:
        return False
    if firebase_admin._apps:
        return True

    credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
    if not credentials_path or not os.path.exists(credentials_path):
        return False

    cred = credentials.Certificate(credentials_path)
    firebase_admin.initialize_app(cred)
    return True
