from django.core.management.base import BaseCommand
from django.utils import timezone
from deals.models import Deal
from payments.payaza import payout_seller


class Command(BaseCommand):
    help = 'Auto-release funds for deals past delivery window'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        deals = Deal.objects.filter(
            status='SHIPPED',
            auto_release_at__lte=now
        )
        if not deals:
            self.stdout.write(self.style.WARNING('No deals to auto-release'))
            return

        for deal in deals:
            try:
                payout_seller(deal)
                deal.status = 'COMPLETED'
                deal.completed_at = now
                deal.save()
                self.stdout.write(self.style.SUCCESS(f'Released {deal.id}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed {deal.id}: {e}'))
