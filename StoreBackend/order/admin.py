from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse
from django.utils.formats import number_format

from .models import Order, OrderItem, Checkout, CheckoutItem, StoreSettings
from django.conf import settings

# EXPORT LIBRARIES
import openpyxl
from openpyxl.styles import Font
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


# ---------------------------------------------------------------------------
# INLINE: ORDER ITEMS
# ---------------------------------------------------------------------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total_price_display']
    fields = ['product', 'quantity', 'price_at_purchase', 'total_price_display']

    def total_price_display(self, obj):
        try:
            if obj.price_at_purchase:
                total = obj.price_at_purchase * obj.quantity
                formatted = number_format(total, decimal_pos=2)
                return f"₹{formatted}"
            return "N/A"
        except:
            return "Error"

    total_price_display.short_description = 'Total Price'


# ---------------------------------------------------------------------------
# ORDER ADMIN
# ---------------------------------------------------------------------------
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = [
        'id', 'user_display', 'status_display', 'payment_status_display',
        'total_amount_display', 'items_count', 'shipping_address_display',
        'created_at', 'payment_info_status'
    ]

    list_filter = ['status', 'payment_status', 'created_at', 'updated_at']

    search_fields = [
        'id', 'user__email', 'user__username', 'user__first_name',
        'user__last_name', 'shipping_address__address_line1',
        'shipping_address__city', 'notes'
    ]

    readonly_fields = ['created_at', 'updated_at', 'total_amount_display', 'payment_qr_data']

    inlines = [OrderItemInline]
    list_per_page = 25
    list_select_related = ['user', 'shipping_address']

    fieldsets = (
        ('Order Information', {'fields': ('user', 'status', 'notes')}),
        ('Shipping', {'fields': ('shipping_address',)}),
        ('Payment Management (Admin Only)', {
            'fields': ('payment_status',),
            'description': '⚠️ Only admins can change payment status.'
        }),
        ('Payment Information', {
            'fields': ('payment_qr_data',),
            'description': 'UPI payment QR data (auto-generated).'
        }),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    actions = [
        'mark_payment_paid', 'mark_payment_failed', 'mark_payment_refunded',
        'regenerate_payment_data', 'mark_as_confirmed', 'mark_as_shipped',
        'mark_as_delivered', 'mark_as_cancelled', 'bulk_status_update',
        'export_orders_excel'
    ]


    # -------------------------------------------------------------------
    # EXPORT EXCEL
    # -------------------------------------------------------------------
    def export_orders_excel(self, request, queryset):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Orders"

        headers = [
            "Order ID", "Customer Name", "Email", "Address", "City", "State", "Pincode",
            "Product", "Qty", "Price", "Total",
            "Order Status", "Payment Status", "Created At"
        ]
        ws.append(headers)
        
        # Adding extra space between headers and content
        row = 2  # Start the content from row 2
        for col in range(1, len(headers) + 1):
            ws.cell(row=1, column=col).font = Font(bold=True)
        
        user_order_map = {}
        
        for order in queryset:
            address = order.shipping_address
            customer_key = (order.user.get_full_name(), order.user.email, address.address_line1, address.city, address.state, address.pincode)
            
            if customer_key not in user_order_map:
                user_order_map[customer_key] = {'order_id': order.id, 'user_name': order.user.get_full_name(), 'email': order.user.email,
                                                'address': address.address_line1, 'city': address.city, 'state': address.state, 'pincode': address.pincode,
                                                'status': order.get_status_display(), 'payment_status': order.get_payment_status_display(), 
                                                'created_at': order.created_at.strftime("%Y-%m-%d %H:%M"), 'items': []}
            
            for item in order.items.all():
                total_price = item.price_at_purchase * item.quantity
                user_order_map[customer_key]['items'].append({
                    'product': item.product.name,
                    'quantity': item.quantity,
                    'price_at_purchase': item.price_at_purchase,
                    'total_price': total_price
                })
        
        # Now add data to sheet
        for user_data in user_order_map.values():
            for item in user_data['items']:
                ws.append([
                    user_data['order_id'],
                    user_data['user_name'],
                    user_data['email'],
                    user_data['address'],
                    user_data['city'],
                    user_data['state'],
                    user_data['pincode'],
                    item['product'],
                    item['quantity'],
                    float(item['price_at_purchase']),
                    float(item['total_price']),
                    user_data['status'],
                    user_data['payment_status'],
                    user_data['created_at']
                ])
                row += 1

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename=\"orders.xlsx\"'
        wb.save(response)
        return response

    export_orders_excel.short_description = "Download selected orders as Excel (.xlsx)"


    # -------------------------------------------------------------------
    # EXPORT PDF
    # -------------------------------------------------------------------
    def export_orders_pdf(self, request, queryset):
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename=\"orders.pdf\"'

        p = canvas.Canvas(response, pagesize=A4)
        width, height = A4
        y = height - 50

        p.setFont("Helvetica-Bold", 14)
        p.drawString(40, y, "Order Report")
        y -= 25

        for order in queryset:
            if y < 120:
                p.showPage()
                y = height - 50

            addr = order.shipping_address

            p.setFont("Helvetica-Bold", 11)
            p.drawString(20, y, f"Order #{order.id} - {order.user.get_full_name()} ({order.user.email})")
            y -= 16

            p.setFont("Helvetica", 10)
            p.drawString(20, y, f"Address: {addr.address_line1}, {addr.city}, {addr.state} - {addr.pincode}")
            y -= 15

            p.drawString(20, y, f"Status: {order.get_status_display()} | Payment: {order.get_payment_status_display()}")
            y -= 18

            p.setFont("Helvetica-Bold", 10)
            p.drawString(30, y, "Product")
            p.drawString(220, y, "Qty")
            p.drawString(260, y, "Price")
            p.drawString(320, y, "Total")
            y -= 15

            p.setFont("Helvetica", 10)

            for item in order.items.all():

                price = number_format(item.price_at_purchase, decimal_pos=2)
                total = number_format(item.total_price, decimal_pos=2)

                p.drawString(30, y, item.product.name)
                p.drawString(220, y, str(item.quantity))
                p.drawString(260, y, f"₹{price}")
                p.drawString(320, y, f"₹{total}")
                y -= 15

            y -= 10

        p.save()
        return response

    export_orders_pdf.short_description = "Download selected orders as PDF (.pdf)"


    # -------------------------------------------------------------------
    # DISPLAY HELPERS
    # -------------------------------------------------------------------
    def user_display(self, obj):
        user = obj.user
        return format_html(
            "<strong>{}</strong><br><small>{}</small>",
            user.get_full_name(),
            user.email
        )
    user_display.short_description = "Customer"


    def status_display(self, obj):
        colors = {
            "pending": "orange",
            "confirmed": "blue",
            "shipped": "purple",
            "delivered": "green",
            "cancelled": "red"
        }
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>',
            colors.get(obj.status, "black"),
            obj.get_status_display()
        )
    status_display.short_description = "Status"


    def payment_status_display(self, obj):
        colors = {
            "pending": "orange",
            "paid": "green",
            "failed": "red",
            "refunded": "gray"
        }
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>',
            colors.get(obj.payment_status, "black"),
            obj.get_payment_status_display()
        )
    payment_status_display.short_description = "Payment"


    def total_amount_display(self, obj):
        total = 0
        for item in obj.items.all():
            if item.price_at_purchase is not None:
                total += float(item.price_at_purchase) * item.quantity

        formatted_total = number_format(total, decimal_pos=2)

        return format_html(
            '<span style="color:green;">₹{}</span>',
            formatted_total
        )
    total_amount_display.short_description = "Total Amount"


    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = "Items"


    def shipping_address_display(self, obj):
        addr = obj.shipping_address
        return f"{addr.address_line1}, {addr.city}, {addr.state}, {addr.pincode}"
    shipping_address_display.short_description = "Shipping"


    def payment_info_status(self, obj):
        if obj.payment_qr_data:
            return format_html('<span style="color:green;">✔ QR</span>')
        return format_html('<span style="color:red;">✘ No QR</span>')
    payment_info_status.short_description = "Payment Info"


# ---------------------------------------------------------------------------
# INLINE: CHECKOUT ITEMS
# ---------------------------------------------------------------------------
class CheckoutItemInline(admin.TabularInline):
    model = CheckoutItem
    extra = 0
    readonly_fields = ['total_price_display']
    fields = ['product', 'quantity', 'price_at_checkout', 'total_price_display']

    def total_price_display(self, obj):
        if obj.price_at_checkout:
            total = obj.price_at_checkout * obj.quantity
            formatted = number_format(total, decimal_pos=2)
            return f"₹{formatted}"
        return "N/A"

    total_price_display.short_description = "Total Price"


# ---------------------------------------------------------------------------
# CHECKOUT ADMIN
# ---------------------------------------------------------------------------
@admin.register(Checkout)
class CheckoutAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_display', 'items_count',
        'expires_at', 'time_remaining', 'status_display', 'created_at'
    ]

    list_filter = ['is_active', 'created_at', 'expires_at']

    search_fields = [
        'id', 'user__email', 'user__username',
    ]

    readonly_fields = ['created_at', 'updated_at', 'time_remaining', 'status_display']

    inlines = [CheckoutItemInline]
    list_per_page = 25
    list_select_related = ['user']

    fieldsets = (
        ('Checkout Information', {'fields': ('user',)}),
        ('Expiration', {'fields': ('expires_at', 'is_active')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    actions = ['mark_expired', 'extend_checkout', 'delete_expired_checkouts']


    def user_display(self, obj):
       return f"{obj.user.get_full_name()} ({obj.user.email})"
    user_display.short_description = "Customer"


    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = "Items"


    def time_remaining(self, obj):
        if obj.is_expired():
            return format_html('<span style="color:red;">Expired</span>')

        remaining = obj.time_until_expiry()
        minutes = int(remaining.total_seconds() / 60)
        return f"{minutes} min"
    time_remaining.short_description = "Remaining"


    def status_display(self, obj):
        if obj.is_expired():
            return format_html('<span style="color:red;">Expired</span>')
        if obj.is_active:
            return format_html('<span style="color:green;">Active</span>')
        return format_html('<span style="color:gray;">Inactive</span>')
    status_display.short_description = "Status"


    def mark_expired(self, request, queryset):
        updated = 0
        for checkout in queryset:
            checkout.mark_expired()
            updated += 1
        self.message_user(request, f"Marked {updated} checkouts as expired")
    mark_expired.short_description = "Mark as expired"


    def extend_checkout(self, request, queryset):
        expiry_hours = getattr(settings, "CHECKOUT_EXPIRY_HOURS", 2)
        updated = queryset.update(
            expires_at=timezone.now() + timedelta(hours=expiry_hours)
        )
        self.message_user(request, f"Extended {updated} checkouts")
    extend_checkout.short_description = "Extend expiration"


    def delete_expired_checkouts(self, request, queryset):
        expired = queryset.filter(is_active=False, expires_at__lt=timezone.now())
        count = expired.count()
        expired.delete()
        self.message_user(request, f"Deleted {count} expired checkouts")
    delete_expired_checkouts.short_description = "Delete expired checkouts"


admin.site.register(StoreSettings)