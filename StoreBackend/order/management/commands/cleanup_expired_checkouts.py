from django.core.management.base import BaseCommand
from django.utils import timezone
from order.models import Checkout


class Command(BaseCommand):
    help = 'Clean up expired checkouts and return items to inventory'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned up without actually doing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find all expired checkouts
        expired_checkouts = Checkout.objects.filter(
            is_active=True,
            expires_at__lt=timezone.now()
        )
        
        if not expired_checkouts.exists():
            self.stdout.write(
                self.style.SUCCESS('No expired checkouts found.')
            )
            return
        
        self.stdout.write(
            f'Found {expired_checkouts.count()} expired checkout(s)'
        )
        
        if dry_run:
            self.stdout.write('DRY RUN - No changes will be made')
            for checkout in expired_checkouts:
                self.stdout.write(
                    f'  - Checkout #{checkout.id} by {checkout.user} '
                    f'(expired at {checkout.expires_at})'
                )
            return
        
        # Process expired checkouts
        processed_count = 0
        for checkout in expired_checkouts:
            try:
                checkout.mark_expired()
                processed_count += 1
                self.stdout.write(
                    f'  ✅ Processed checkout #{checkout.id} by {checkout.user}'
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'  ❌ Error processing checkout #{checkout.id}: {e}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {processed_count} expired checkout(s)'
            )
        )
