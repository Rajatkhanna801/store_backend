from django.core.management.base import BaseCommand
from order.models import OrderItem
from inventory.models import Product

class Command(BaseCommand):
    help = 'Fix order items with None prices by setting them to product current prices'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without actually doing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find order items with None prices
        items_with_none_prices = OrderItem.objects.filter(price_at_purchase__isnull=True)
        
        if not items_with_none_prices.exists():
            self.stdout.write(
                self.style.SUCCESS('No order items with None prices found.')
            )
            return
        
        self.stdout.write(
            f'Found {items_with_none_prices.count()} order items with None prices'
        )
        
        fixed_count = 0
        for item in items_with_none_prices:
            if item.product:
                # Get current product price
                if hasattr(item.product, 'effective_price'):
                    new_price = item.product.effective_price
                elif hasattr(item.product, 'price'):
                    new_price = item.product.price
                else:
                    new_price = 0
                
                if not dry_run:
                    item.price_at_purchase = new_price
                    item.save()
                    self.stdout.write(
                        f'Fixed OrderItem #{item.id}: {item.product.name} - '
                        f'Price set to {new_price}'
                    )
                else:
                    self.stdout.write(
                        f'Would fix OrderItem #{item.id}: {item.product.name} - '
                        f'Price would be set to {new_price}'
                    )
                fixed_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'OrderItem #{item.id} has no product - cannot fix price'
                    )
                )
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Dry run complete. Would fix {fixed_count} order items.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully fixed {fixed_count} order items with None prices.'
                )
            )
