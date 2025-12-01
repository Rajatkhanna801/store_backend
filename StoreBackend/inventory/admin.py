from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.formats import number_format

from .models import Category, Product, ProductImage


# ---------------------------------------------------------
# INLINE FOR PRODUCT IMAGES
# ---------------------------------------------------------
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ["image", "alt_text", "sort_order"]
    show_change_link = True


# ---------------------------------------------------------
# PRODUCT ADMIN
# ---------------------------------------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "thumbnail",
        "name",
        "category",
        "price_display",
        "discounted_price_display",
        "effective_price_display",
        "quantity_display",
        "status_display",
        "created_at",
    ]

    list_filter = ["category", "created_at", "updated_at"]
    search_fields = ["name", "description", "category__name"]

    readonly_fields = [
        "created_at",
        "updated_at",
        "effective_price_display",
        "images_gallery",
    ]

    inlines = [ProductImageInline]
    list_per_page = 25
    list_select_related = ["category"]

    fieldsets = (
        ("Product Information", {
            "fields": ("name", "category", "description")
        }),
        ("Pricing", {
            "fields": ("price", "discounted_price", "effective_price_display")
        }),
        ("Inventory", {
            "fields": ("quantity",)
        }),
        ("Product Images", {
            "fields": ("images_gallery",),
            "description": "All images linked to this product"
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    actions = [
        "mark_as_in_stock",
        "mark_as_out_of_stock",
        "apply_discount",
        "remove_discount",
    ]

    # ---------------------------------------------------
    # IMAGE THUMBNAIL IN LIST VIEW
    # ---------------------------------------------------
    def thumbnail(self, obj):
        img = obj.images.order_by("sort_order").first()
        if img and img.image:
            return mark_safe(
                f'<img src="{img.image.url}" width="55" height="55" '
                f'style="object-fit:cover; border-radius:5px;" />'
            )
        return "—"

    thumbnail.short_description = "Image"

    # ---------------------------------------------------
    # IMAGE GALLERY IN DETAIL PAGE
    # ---------------------------------------------------
    def images_gallery(self, obj):
        images = obj.images.all().order_by("sort_order")
        if not images:
            return "No images uploaded"

        html = ""
        for img in images:
            html += f"""
                <div style='margin:5px; display:inline-block;'>
                    <img src='{img.image.url}'
                        style='width:120px; height:120px; object-fit:cover;
                               border-radius:6px; border:1px solid #ccc;' />
                    <div style='text-align:center; font-size:12px; color:#666;'>
                        {img.alt_text or ""}
                    </div>
                </div>
            """
        return mark_safe(html)

    images_gallery.short_description = "Product Images"

    # ---------------------------------------------------
    # PRICE DISPLAY FIXED (No SafeString Errors)
    # ---------------------------------------------------
    def price_display(self, obj):
        if obj.price is not None:
            formatted = number_format(obj.price, decimal_pos=2)
            return format_html(
                '<span style="color:#28A745; font-weight:bold;">₹{}</span>',
                formatted
            )
        return "N/A"

    price_display.short_description = "Base Price"

    def discounted_price_display(self, obj):
        if obj.discounted_price:
            formatted = number_format(obj.discounted_price, decimal_pos=2)
            return format_html(
                '<span style="color:#FF6B35; font-weight:bold;">₹{}</span>',
                formatted
            )
        return "—"

    discounted_price_display.short_description = "Discounted Price"

    def effective_price_display(self, obj):
        price = obj.effective_price
        if price is None:
            return "—"

        formatted = number_format(price, decimal_pos=2)

        if obj.discounted_price and obj.discounted_price < obj.price:
            return format_html(
                '<span style="color:#DC3545; font-weight:bold;">₹{} (Discounted)</span>',
                formatted
            )

        return format_html(
            '<span style="color:#28A745; font-weight:bold;">₹{}</span>',
            formatted
        )

    effective_price_display.short_description = "Effective Price"

    # ---------------------------------------------------
    # STOCK INDICATORS
    # ---------------------------------------------------
    def quantity_display(self, obj):
        if obj.quantity == 0:
            return format_html('<span style="color:#DC3545; font-weight:bold;">Out of Stock</span>')
        elif obj.quantity <= 5:
            return format_html('<span style="color:#FFC107; font-weight:bold;">Low Stock ({})</span>', obj.quantity)
        return format_html('<span style="color:#28A745;">{}</span>', obj.quantity)

    quantity_display.short_description = "Stock"

    def status_display(self, obj):
        if obj.quantity == 0:
            return format_html('<span style="color:#DC3545; font-weight:bold;">Out of Stock</span>')
        if obj.discounted_price and obj.discounted_price < obj.price:
            return format_html('<span style="color:#FF6B35; font-weight:bold;">On Sale</span>')
        return format_html('<span style="color:#28A745;">Available</span>')

    status_display.short_description = "Status"

    # ---------------------------------------------------
    # ACTIONS
    # ---------------------------------------------------
    def mark_as_in_stock(self, request, queryset):
        updated = queryset.update(quantity=10)
        self.message_user(request, f"{updated} products marked as in stock")

    def mark_as_out_of_stock(self, request, queryset):
        updated = queryset.update(quantity=0)
        self.message_user(request, f"{updated} products marked as out of stock")

    def apply_discount(self, request, queryset):
        updated = 0
        for p in queryset:
            if p.price:
                p.discounted_price = p.price - (p.price * 0.1)
                p.save()
                updated += 1
        self.message_user(request, f"Applied 10% discount to {updated} products")

    def remove_discount(self, request, queryset):
        updated = queryset.update(discounted_price=None)
        self.message_user(request, f"Removed discount from {updated} products")


# ---------------------------------------------------------
# CATEGORY ADMIN (WITH ICON SUPPORT)
# ---------------------------------------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = ["id", "icon_preview", "name", "description_preview", "products_count", "created_at"]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["name", "description"]

    readonly_fields = ["created_at", "updated_at", "products_count", "icon_preview"]

    fieldsets = (
        ("Category Information", {
            "fields": ("name", "description", "icon", "icon_preview")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    list_per_page = 25
    actions = ["merge_categories"]

    # ----------------------------------------------
    # ICON PREVIEW
    # ----------------------------------------------
    def icon_preview(self, obj):
        if obj.icon:
            return mark_safe(
                f'<img src="{obj.icon.url}" width="50" height="50" '
                f'style="object-fit:contain; border-radius:4px;" />'
            )
        return "—"

    icon_preview.short_description = "Icon"

    # ----------------------------------------------
    # DESCRIPTION PREVIEW
    # ----------------------------------------------
    def description_preview(self, obj):
        if obj.description:
            return obj.description[:50] + ("..." if len(obj.description) > 50 else "")
        return "No description"

    description_preview.short_description = "Description"

    # ----------------------------------------------
    # PRODUCTS COUNT
    # ----------------------------------------------
    def products_count(self, obj):
        count = obj.products.count()
        if count == 0:
            return format_html('<span style="color:#6C757D;">0</span>')
        if count == 1:
            return format_html('<span style="color:#28A745;">1</span>')
        return format_html('<span style="color:#007BFF;">{} products</span>', count)

    products_count.short_description = "Products"

    # ----------------------------------------------
    # MERGE CATEGORIES
    # ----------------------------------------------
    def merge_categories(self, request, queryset):
        if queryset.count() < 2:
            self.message_user(request, "Select at least 2 categories to merge")
            return

        target = queryset.first()
        others = queryset.exclude(id=target.id)

        for c in others:
            c.products.update(category=target)
            c.delete()

        self.message_user(
            request,
            f"Merged {others.count()} categories into '{target.name}'"
        )

    merge_categories.short_description = "Merge selected categories"
