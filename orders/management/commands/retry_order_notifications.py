from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from orders.models import OrderNotification
from orders.services import send_order_notifications


class Command(BaseCommand):
    help = "Retry pending or failed order email notifications."

    def add_arguments(self, parser):
        parser.add_argument("--max-attempts", type=int, default=5)
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        stale = timezone.now() - timedelta(minutes=10)
        notifications = OrderNotification.objects.filter(attempts__lt=options["max_attempts"]).filter(
            Q(status__in=("pending", "failed")) | Q(status="sending", last_attempt_at__lt=stale)
        ).order_by("last_attempt_at", "pk")[:options["limit"]]
        sent = failed = 0
        for notification in notifications:
            if send_order_notifications(notification.order_id):
                sent += 1
            else:
                failed += 1
        self.stdout.write(f"Retried {sent + failed}: {sent} sent, {failed} failed or skipped.")
