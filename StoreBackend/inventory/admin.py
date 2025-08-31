from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Q
from .models import Category, Product, ProductImage


# Inline for adding multiple images inside Product admin
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ["image", "alt_text", "sort_order"]
    readonly_fields = []
    show_change_link = True


# Product admin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "id", "name", "category", "price_display", "discounted_price_display", 
        "effective_price_display", "quantity_display", "status_display", "created_at"
    ]
    list_filter = [
        "category", 
        "created_at", 
        "updated_at",
    ]
    search_fields = ["name", "description", "category__name"]
    readonly_fields = ["created_at", "updated_at", "effective_price_display"]
    inlines = [ProductImageInline]
    list_per_page = 25
    list_select_related = ["category"]
    
    fieldsets = (
        ('Product Information', {
            'fields': ('name', 'category', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'discounted_price', 'effective_price_display'),
            'description': 'Set base price and optional discounted price'
        }),
        ('Inventory', {
            'fields': ('quantity',),
            'description': 'Current stock quantity'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_in_stock', 'mark_as_out_of_stock', 'apply_discount', 'remove_discount']
    
    def price_display(self, obj):
        """Display price with formatting"""
        if obj.price:
            # Pre-format the price to avoid format_html issues
            formatted_price = f"{obj.price:.2f}"
            return format_html(
                '<span style="color: #28A745; font-weight: bold;">₹{}</span>',
                formatted_price
            )
        return "N/A"
    price_display.short_description = 'Base Price'
    
    def discounted_price_display(self, obj):
        """Display discounted price with formatting"""
        if obj.discounted_price:
            # Pre-format the price to avoid format_html issues
            formatted_price = f"{obj.discounted_price:.2f}"
            return format_html(
                '<span style="color: #FF6B35; font-weight: bold;">₹{}</span>',
                formatted_price
            )
        return "—"
    discounted_price_display.short_description = 'Discounted Price'
    
    def effective_price_display(self, obj):
        """Display effective price (discounted or base)"""
        try:
            effective_price = obj.effective_price
            if effective_price:
                if obj.discounted_price and obj.discounted_price < obj.price:
                    # Pre-format the price to avoid format_html issues
                    formatted_price = f"{effective_price:.2f}"
                    return format_html(
                        '<span style="color: #DC3545; font-weight: bold;">₹{} (Discounted)</span>',
                        formatted_price
                    )
                else:
                    # Pre-format the price to avoid format_html issues
                    formatted_price = f"{effective_price:.2f}"
                    return format_html(
                        '<span style="color: #28A745; font-weight: bold;">₹{}</span>',
                        formatted_price
                    )
        except:
            pass
        return "Error"
    effective_price_display.short_description = 'Effective Price'
    
    def quantity_display(self, obj):
        """Display quantity with color coding"""
        if obj.quantity == 0:
            return format_html(
                '<span style="color: #DC3545; font-weight: bold;">Out of Stock</span>'
            )
        elif obj.quantity <= 5:
            # Pre-format the quantity to avoid format_html issues
            formatted_quantity = str(obj.quantity)
            return format_html(
                '<span style="color: #FFC107; font-weight: bold;">Low Stock ({})</span>',
                formatted_quantity
            )
        else:
            # Pre-format the quantity to avoid format_html issues
            formatted_quantity = str(obj.quantity)
            return format_html(
                '<span style="color: #28A745;">{}</span>',
                formatted_quantity
            )
    quantity_display.short_description = 'Stock'
    
    def status_display(self, obj):
        """Display product status"""
        if obj.quantity == 0:
            return format_html(
                '<span style="color: #DC3545; font-weight: bold;">Out of Stock</span>'
            )
        elif obj.discounted_price and obj.discounted_price < obj.price:
            return format_html(
                '<span style="color: #FF6B35; font-weight: bold;">On Sale</span>'
            )
        else:
            return format_html(
                '<span style="color: #28A745;">Available</span>'
            )
    status_display.short_description = 'Status'
    
    def mark_as_in_stock(self, request, queryset):
        """Mark selected products as in stock"""
        updated = queryset.update(quantity=10)
        self.message_user(request, f"{updated} products marked as in stock")
    mark_as_in_stock.short_description = "Mark as in stock (set quantity to 10)"
    
    def mark_as_out_of_stock(self, request, queryset):
        """Mark selected products as out of stock"""
        updated = queryset.update(quantity=0)
        self.message_user(request, f"{updated} products marked as out of stock")
    mark_as_out_of_stock.short_description = "Mark as out of stock (set quantity to 0)"
    
    def apply_discount(self, request, queryset):
        """Apply 10% discount to selected products"""
        updated = 0
        for product in queryset:
            if product.price:
                discount_amount = product.price * 0.1
                product.discounted_price = product.price - discount_amount
                product.save()
                updated += 1
        self.message_user(request, f"Applied 10% discount to {updated} products")
    apply_discount.short_description = "Apply 10%% discount"
    
    def remove_discount(self, request, queryset):
        """Remove discount from selected products"""
        updated = queryset.update(discounted_price=None)
        self.message_user(request, f"Removed discount from {updated} products")
    remove_discount.short_description = "Remove discount"


# Category admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "description_preview", "products_count", "created_at"]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at", "products_count"]
    list_per_page = 25
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['merge_categories']
    
    def description_preview(self, obj):
        """Show first 50 characters of description"""
        if obj.description:
            return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
        return "No description"
    description_preview.short_description = 'Description'
    
    def products_count(self, obj):
        """Show count of products in this category"""
        count = obj.products.count()
        if count == 0:
            return format_html(
                '<span style="color: #6C757D;">0 products</span>'
            )
        elif count == 1:
            return format_html(
                '<span style="color: #28A745;">1 product</span>'
            )
        else:
            # Pre-format the count to avoid format_html issues
            formatted_count = str(count)
            return format_html(
                '<span style="color: #007BFF;">{} products</span>',
                formatted_count
            )
    products_count.short_description = 'Products'
    
    def merge_categories(self, request, queryset):
        """Merge selected categories into the first one"""
        if queryset.count() < 2:
            self.message_user(request, "Please select at least 2 categories to merge")
            return
        
        target_category = queryset.first()
        categories_to_merge = queryset.exclude(id=target_category.id)
        
        # Move all products to target category
        for category in categories_to_merge:
            category.products.update(category=target_category)
            category.delete()
        
        self.message_user(
            request, 
            f"Successfully merged {categories_to_merge.count()} categories into '{target_category.name}'"
        )
    merge_categories.short_description = "Merge selected categories into first category"
