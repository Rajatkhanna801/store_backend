from django.contrib import admin
from django.utils.html import format_html
from .models import Cart, CartItem

class CartItemInline(admin.TabularInline):
    """Inline display of cart items within cart"""
    model = CartItem
    extra = 1  # Allow adding new items
    readonly_fields = ['product_display', 'total_price_display']
    fields = ['product', 'product_display', 'quantity', 'status', 'total_price_display']
    
    def product_display(self, obj):
        """Display product with ID and name"""
        if obj.product:
            return f"#{obj.product.id} - {obj.product.name}"
        return "No product"
    product_display.short_description = 'Product'
    
    def total_price_display(self, obj):
        """Display total price for cart item"""
        try:
            # Check if this is a new item (not saved yet)
            if not obj.pk:
                return "Save to calculate"
            
            # Check if product exists and is properly loaded
            if obj.product and hasattr(obj.product, 'effective_price'):
                try:
                    price = obj.product.effective_price
                    if price is not None:
                        total = price * obj.quantity
                        return f"₹{total:.2f}"
                except (TypeError, ValueError):
                    pass
            
            # Fallback to regular price
            if obj.product and hasattr(obj.product, 'price'):
                try:
                    price = obj.product.price
                    if price is not None:
                        total = price * obj.quantity
                        return f"₹{total:.2f}"
                except (TypeError, ValueError):
                    pass
            
            # If no price available
            if obj.product:
                return "Price unavailable"
            else:
                return "No product"
                
        except Exception:
            return "Error"
    total_price_display.short_description = 'Total Price'
    
    def get_queryset(self, request):
        """Optimize queryset to avoid N+1 queries"""
        return super().get_queryset(request).select_related('product')

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_display', 'items_count', 'total_amount_display', 
        'created_at', 'updated_at'
    ]
    list_filter = [
        'created_at', 
        'updated_at',
    ]
    search_fields = ['id', 'user__email', 'user__first_name', 'user__last_name', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'total_amount_display']
    inlines = [CartItemInline]
    
    fieldsets = (
        ('Cart Information', {
            'fields': ('user',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_display(self, obj):
        """Display user information with email"""
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
                ' '.join(user_info[:2]),  # Name and username
                user_info[2] if len(user_info) > 2 else ''  # Email
            )
        return "No User"
    user_display.short_description = 'User'
    
    def items_count(self, obj):
        """Display count of items in cart"""
        count = obj.items.count()
        if count == 0:
            return format_html(
                '<span style="color: orange;">0 items</span>'
            )
        elif count == 1:
            return format_html(
                '<span style="color: green;">1 item</span>'
            )
        else:
            return format_html(
                '<span style="color: blue;">{} items</span>',
                count
            )
    items_count.short_description = 'Items'
    
    def total_amount_display(self, obj):
        """Display total cart amount"""
        try:
            # Use the fixed subtotal method from the model
            total = obj.subtotal()
            
            if total == 0:
                return format_html(
                    '<span style="color: orange;">₹0.00</span>'
                )
            else:
                # Pre-format the number to avoid format_html issues
                formatted_total = f"{float(total):.2f}"
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
    total_amount_display.short_description = 'Total Amount'
    
    actions = ['clear_cart_items', 'mark_items_saved_for_later']
    
    def clear_cart_items(self, request, queryset):
        """Clear all items from selected carts"""
        updated = 0
        for cart in queryset:
            items_count = cart.items.count()
            if items_count > 0:
                cart.items.all().delete()
                updated += 1
        
        if updated:
            self.message_user(
                request, 
                f"Cleared items from {updated} cart(s)."
            )
        else:
            self.message_user(request, "No carts had items to clear.")
    clear_cart_items.short_description = "Clear all items from selected carts"
    
    def mark_items_saved_for_later(self, request, queryset):
        """Mark all cart items as saved for later"""
        from .models import CartItem
        updated = 0
        for cart in queryset:
            items_updated = cart.items.filter(status=CartItem.Status.ACTIVE).update(
                status=CartItem.Status.SAVED
            )
            if items_updated > 0:
                updated += 1
        
        if updated:
            self.message_user(
                request, 
                f"Marked items as saved for later in {updated} cart(s)."
            )
        else:
            self.message_user(request, "No active items found to update.")
    mark_items_saved_for_later.short_description = "Mark items as saved for later"
