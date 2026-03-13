from django.core.management.base import BaseCommand

from services.notification_service import send_deadline_reminders


class Command(BaseCommand):
    help = "Send deadline notifications for 7/3/1 day reminders."

    def handle(self, *args, **options):
        results = send_deadline_reminders()
        total_sent = sum(item.get("sent", 0) for item in results)
        self.stdout.write(self.style.SUCCESS(f"Deadline reminder processing complete. Sent count: {total_sent}"))
