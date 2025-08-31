from django.contrib import admin
from django.utils.html import format_html

from django.utils import timezone
from datetime import timedelta
from .models import Order, OrderItem, Checkout, CheckoutItem
from django.conf import settings

class OrderItemInline(admin.TabularInline):
    """Inline display of order items"""
    model = OrderItem
    extra = 0
    readonly_fields = ['total_price_display']
    fields = ['product', 'quantity', 'price_at_purchase', 'total_price_display']
    
    def total_price_display(self, obj):
        """Display total price for order item"""
        try:
            if obj.price_at_purchase:
                total = obj.price_at_purchase * obj.quantity
                return f"₹{total:.2f}"
            return "N/A"
        except:
            return "Error"
    total_price_display.short_description = 'Total Price'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_display', 'status_display', 'payment_status_display', 
        'total_amount_display', 'items_count', 'shipping_address_display', 
        'created_at', 'payment_info_status'
    ]
    list_filter = [
        'status', 
        'payment_status', 
        'created_at', 
        'updated_at',
    ]
    search_fields = [
        'id', 'user__email', 'user__username', 'user__first_name', 'user__last_name',
        'shipping_address__address_line1', 'shipping_address__city',
        'notes'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'total_amount_display', 'payment_qr_data'
    ]
    inlines = [OrderItemInline]
    list_per_page = 25
    list_select_related = ['user', 'shipping_address']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'status', 'notes')
        }),
        ('Shipping', {
            'fields': ('shipping_address',)
        }),
        ('Payment Management (Admin Only)', {
            'fields': ('payment_status',),
            'description': '⚠️ Only admins can change payment status. Users cannot modify this through API.',
            'classes': ('collapse',)
        }),
        ('Payment Information', {
            'fields': ('payment_qr_data',),
            'description': 'UPI payment data for order (auto-generated, read-only)'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'mark_payment_paid', 'mark_payment_failed', 'mark_payment_refunded',
        'regenerate_payment_data', 'mark_as_confirmed', 'mark_as_shipped',
        'mark_as_delivered', 'mark_as_cancelled', 'bulk_status_update'
    ]
    
    def user_display(self, obj):
        """Display user information"""
        if obj.user:
            user_info = []
            if obj.user.first_name or obj.user.last_name:
                full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
                if full_name:
                    user_info.append(full_name)
            
            user_info.append(f"@{obj.user.username}")
            user_info.append(f"({obj.user.email})")
            
            return format_html(
                '<div style="min-width: 200px;">'
                '<strong>{}</strong><br>'
                '<small style="color: #666;">{}</small>'
                '</div>',
                ' '.join(user_info[:2]),
                user_info[2] if len(user_info) > 2 else ''
            )
        return "No User"
    user_display.short_description = 'User'
    
    def status_display(self, obj):
        """Display order status with color coding"""
        status_colors = {
            'pending': '#FFC107',      # Yellow
            'confirmed': '#17A2B8',    # Blue
            'shipped': '#6F42C1',      # Purple
            'delivered': '#28A745',    # Green
            'cancelled': '#DC3545'     # Red
        }
        color = status_colors.get(obj.status, '#6C757D')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def payment_status_display(self, obj):
        """Display payment status with color coding"""
        status_colors = {
            'pending': '#FFC107',      # Yellow
            'paid': '#28A745',         # Green
            'failed': '#DC3545',       # Red
            'refunded': '#6C757D'      # Gray
        }
        color = status_colors.get(obj.payment_status, '#6C757D')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_payment_status_display()
        )
    payment_status_display.short_description = 'Payment'
    
    def total_amount_display(self, obj):
        """Display total order amount"""
        try:
            # Calculate total manually to avoid property issues
            total = 0
            for item in obj.items.all():
                if item.price_at_purchase is not None:
                    total += float(item.price_at_purchase) * item.quantity
                else:
                    # If price is None, try to get from product
                    if item.product:
                        if hasattr(item.product, 'effective_price') and item.product.effective_price:
                            total += float(item.product.effective_price) * item.quantity
                        elif hasattr(item.product, 'price') and item.product.price:
                            total += float(item.product.price) * item.quantity
            
            if total == 0:
                return format_html(
                    '<span style="color: orange;">₹0.00</span>'
                )
            else:
                # Pre-format the number to avoid format_html issues
                formatted_total = f"{total:.2f}"
                return format_html(
                    '<span style="color: green; font-weight: bold;">₹{}</span>',
                    formatted_total
                )
        except Exception as e:
            # For debugging - show the actual error
            error_msg = str(e)
            return format_html(
                '<span style="color: red;" title="Error: {}">Error: {}</span>',
                error_msg,
                error_msg[:30] + "..." if len(error_msg) > 30 else error_msg
            )
    total_amount_display.short_description = 'Total'
    
    def items_count(self, obj):
        """Display count of items in order"""
        count = obj.items.count()
        if count == 0:
            return format_html('<span style="color: red;">0 items</span>')
        elif count == 1:
            return format_html('<span style="color: green;">1 item</span>')
        else:
            return format_html('<span style="color: blue;">{} items</span>', count)
    items_count.short_description = 'Items'
    
    def shipping_address_display(self, obj):
        """Display shipping address"""
        if obj.shipping_address:
            address = obj.shipping_address
            return format_html(
                '<div style="min-width: 200px;">'
                '<strong>{}</strong><br>'
                '<small style="color: #666;">{}, {}</small>'
                '</div>',
                address.address_line1,
                address.city, address.state
            )
        return "No Address"
    shipping_address_display.short_description = 'Shipping Address'
    
    def payment_info_status(self, obj):
        """Display payment info status"""
        if obj.payment_qr_data:
            return format_html(
                '<span style="color: green;">✓ UPI Data</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">✗ No UPI Data</span>'
            )
    payment_info_status.short_description = 'Payment Info'
    
    def mark_payment_paid(self, request, queryset):
        """Mark selected orders as paid"""
        updated = queryset.update(payment_status='paid')
        self.message_user(request, f"{updated} orders marked as paid")
    mark_payment_paid.short_description = "Mark as paid"
    
    def mark_payment_failed(self, request, queryset):
        """Mark selected orders as payment failed"""
        updated = queryset.update(payment_status='failed')
        self.message_user(request, f"{updated} orders marked as payment failed")
    mark_payment_failed.short_description = "Mark as payment failed"
    
    def mark_payment_refunded(self, request, queryset):
        """Mark selected orders as refunded"""
        updated = queryset.update(payment_status='refunded')
        self.message_user(request, f"{updated} orders marked as refunded")
    mark_payment_refunded.short_description = "Mark as refunded"
    
    def regenerate_payment_data(self, request, queryset):
        """Regenerate UPI payment data for selected orders"""
        from .utils import generate_upi_payment_data
        updated = 0
        for order in queryset:
            try:
                order.payment_qr_data = generate_upi_payment_data(
                    order.total_amount(), order.id
                )
                order.save()
                updated += 1
            except:
                pass
        self.message_user(request, f"Regenerated payment data for {updated} orders")
    regenerate_payment_data.short_description = "Regenerate payment data"
    
    def mark_as_confirmed(self, request, queryset):
        """Mark selected orders as confirmed"""
        updated = queryset.update(status='confirmed')
        self.message_user(request, f"{updated} orders marked as confirmed")
    mark_as_confirmed.short_description = "Mark as confirmed"
    
    def mark_as_shipped(self, request, queryset):
        """Mark selected orders as shipped"""
        updated = queryset.update(status='shipped')
        self.message_user(request, f"{updated} orders marked as shipped")
    mark_as_shipped.short_description = "Mark as shipped"
    
    def mark_as_delivered(self, request, queryset):
        """Mark selected orders as delivered"""
        updated = queryset.update(status='delivered')
        self.message_user(request, f"{updated} orders marked as delivered")
    mark_as_delivered.short_description = "Mark as delivered"
    
    def mark_as_cancelled(self, request, queryset):
        """Mark selected orders as cancelled"""
        updated = queryset.update(status='cancelled')
        self.message_user(request, f"{updated} orders marked as cancelled")
    mark_as_cancelled.short_description = "Mark as cancelled"
    
    def bulk_status_update(self, request, queryset):
        """Bulk update order statuses"""
        # This is a placeholder for more complex bulk operations
        self.message_user(request, f"Selected {queryset.count()} orders for bulk update")
    bulk_status_update.short_description = "Bulk status update"
    
    def has_change_permission(self, request, obj=None):
        """Ensure only admins can change payment status"""
        if obj and 'payment_status' in request.POST:
            # Log payment status changes for audit
            if obj.payment_status != request.POST.get('payment_status'):
                print(f"Admin {request.user} changed payment status for Order #{obj.id} from {obj.payment_status} to {request.POST.get('payment_status')}")
        return super().has_change_permission(request, obj)

class CheckoutItemInline(admin.TabularInline):
    """Inline display of checkout items"""
    model = CheckoutItem
    extra = 0
    readonly_fields = ['total_price_display']
    fields = ['product', 'quantity', 'price_at_checkout', 'total_price_display']
    
    def total_price_display(self, obj):
        """Display total price for checkout item"""
        try:
            if obj.price_at_checkout:
                total = obj.price_at_checkout * obj.quantity
                return f"₹{total:.2f}"
            return "N/A"
        except:
            return "Error"
    total_price_display.short_description = 'Total Price'

@admin.register(Checkout)
class CheckoutAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_display', 'shipping_address_display', 'items_count',
        'expires_at', 'time_remaining', 'status_display', 'created_at'
    ]
    list_filter = [
        'is_active', 
        'created_at', 
        'expires_at',
    ]
    search_fields = [
        'id', 'user__email', 'user__username', 'user__first_name', 'user__last_name',
        'shipping_address__address_line1', 'shipping_address__city'
    ]
    readonly_fields = ['created_at', 'updated_at', 'time_remaining', 'status_display']
    inlines = [CheckoutItemInline]
    list_per_page = 25
    list_select_related = ['user', 'shipping_address']
    
    fieldsets = (
        ('Checkout Information', {
            'fields': ('user', 'shipping_address')
        }),
        ('Expiration', {
            'fields': ('expires_at', 'is_active'),
            'description': 'Checkout automatically expires after configured time'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_expired', 'extend_checkout', 'delete_expired_checkouts']
    
    def user_display(self, obj):
        """Display user information"""
        if obj.user:
            user_info = []
            if obj.user.first_name or obj.user.last_name:
                full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
                if full_name:
                    user_info.append(full_name)
            
            user_info.append(f"@{obj.user.username}")
            user_info.append(f"({obj.user.email})")
            
            return format_html(
                '<div style="min-width: 200px;">'
                '<strong>{}</strong><br>'
                '<small style="color: #666;">{}</small>'
                '</div>',
                ' '.join(user_info[:2]),
                user_info[2] if len(user_info) > 2 else ''
            )
        return "No User"
    user_display.short_description = 'User'
    
    def shipping_address_display(self, obj):
        """Display shipping address"""
        if obj.shipping_address:
            address = obj.shipping_address
            return format_html(
                '<div style="min-width: 200px;">'
                '<strong>{}</strong><br>'
                '<small style="color: #666;">{}, {}</small>'
                '</div>',
                address.address_line1,
                address.city, address.state
            )
        return "No Address"
    shipping_address_display.short_description = 'Shipping Address'
    
    def items_count(self, obj):
        """Display count of items in checkout"""
        count = obj.items.count()
        if count == 0:
            return format_html('<span style="color: red;">0 items</span>')
        elif count == 1:
            return format_html('<span style="color: green;">1 item</span>')
        else:
            return format_html('<span style="color: blue;">{} items</span>', count)
    items_count.short_description = 'Items'
    
    def time_remaining(self, obj):
        """Display time remaining until expiry"""
        if obj.is_expired():
            return format_html('<span style="color: red;">Expired</span>')
        
        time_left = obj.time_until_expiry()
        hours = time_left.total_seconds() / 3600
        
        if hours < 1:
            minutes = int(time_left.total_seconds() / 60)
            return format_html(
                '<span style="color: orange;">{} min</span>',
                minutes
            )
        elif hours < 24:
            return format_html(
                '<span style="color: blue;">{} hours</span>',
                round(hours, 1)
            )
        else:
            days = hours / 24
            return format_html(
                '<span style="color: green;">{} days</span>',
                round(days, 1)
            )
    time_remaining.short_description = 'Time Remaining'
    
    def status_display(self, obj):
        """Display checkout status"""
        if obj.is_expired():
            return format_html('<span style="color: red;">Expired</span>')
        elif not obj.is_active:
            return format_html('<span style="color: gray;">Inactive</span>')
        else:
            return format_html('<span style="color: green;">Active</span>')
    status_display.short_description = 'Status'
    
    def mark_expired(self, request, queryset):
        """Mark selected checkouts as expired"""
        updated = 0
        for checkout in queryset:
            if checkout.is_active:
                checkout.mark_expired()
                updated += 1
        self.message_user(request, f"Marked {updated} checkouts as expired")
    mark_expired.short_description = "Mark as expired"
    
    def extend_checkout(self, request, queryset):
        """Extend checkout expiration by configured time"""
        from django.conf import settings
        expiry_hours = getattr(settings, 'CHECKOUT_EXPIRY_HOURS', 2)
        updated = 0
        for checkout in queryset:
            if checkout.is_active and not checkout.is_expired():
                checkout.expires_at = timezone.now() + timedelta(hours=expiry_hours)
                checkout.save()
                updated += 1
        self.message_user(
            request, 
            f"Extended {updated} checkouts by {expiry_hours} hours"
        )
    extend_checkout.short_description = f"Extend checkout by {getattr(settings, 'CHECKOUT_EXPIRY_HOURS', 2)} hours"
    
    def delete_expired_checkouts(self, request, queryset):
        """Delete expired checkouts"""
        expired_checkouts = queryset.filter(
            is_active=False,
            expires_at__lt=timezone.now()
        )
        count = expired_checkouts.count()
        expired_checkouts.delete()
        self.message_user(request, f"Deleted {count} expired checkouts")
    delete_expired_checkouts.short_description = "Delete expired checkouts"
