import csv
from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.contrib import messages
from django.utils.safestring import mark_safe
from .models import User, Address


class AddressInline(admin.TabularInline):
    """Inline admin for Address model"""
    model = Address
    extra = 0
    fields = ('label', 'address_line1', 'address_line2', 'city', 'state', 'country', 'pincode', 'is_default')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Custom User admin with CSV export functionality"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    inlines = [AddressInline]
    
    fieldsets = (
        ('Authentication', {
            'fields': ('username', 'email', 'password')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'phone_number')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['export_users_csv']
    
    def get_urls(self):
        """Add custom URLs for export functionality"""
        urls = super().get_urls()
        custom_urls = [
            path('export-csv/', self.admin_site.admin_view(self.export_all_users_csv), name='export_all_users_csv'),
        ]
        return custom_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        """Add export button to changelist view"""
        extra_context = extra_context or {}
        extra_context['export_url'] = 'export-csv/'
        return super().changelist_view(request, extra_context=extra_context)
    
    def export_users_csv(self, request, queryset):
        """Export selected users to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
        
        writer = csv.writer(response)
        
        # Write headers
        headers = [
            'ID', 'Username', 'Email', 'First Name', 'Last Name', 'Phone Number',
            'Is Active', 'Is Staff', 'Is Superuser', 'Date Joined', 'Last Login',
            'Address Count', 'Default Address'
        ]
        writer.writerow(headers)
        
        # Write user data
        for user in queryset:
            # Get address information
            addresses = user.addresses.all()
            address_count = addresses.count()
            default_address = addresses.filter(is_default=True).first()
            default_addr_str = ""
            if default_address:
                default_addr_str = f"{default_address.address_line1}, {default_address.city}, {default_address.pincode}"
            
            writer.writerow([
                user.id,
                user.username,
                user.email,
                user.first_name,
                user.last_name,
                user.phone_number or '',
                user.is_active,
                user.is_staff,
                user.is_superuser,
                user.date_joined.strftime('%Y-%m-%d %H:%M:%S') if user.date_joined else '',
                user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '',
                address_count,
                default_addr_str
            ])
        
        return response
    
    export_users_csv.short_description = "Export selected users to CSV"
    
    def export_all_users_csv(self, request):
        """Export all users to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="all_users_export.csv"'
        
        writer = csv.writer(response)
        
        # Write headers
        headers = [
            'ID', 'Username', 'Email', 'First Name', 'Last Name', 'Phone Number',
            'Is Active', 'Is Staff', 'Is Superuser', 'Date Joined', 'Last Login',
            'Address Count', 'Default Address'
        ]
        writer.writerow(headers)
        
        # Get all users
        users = User.objects.all().select_related().prefetch_related('addresses')
        
        # Write user data
        for user in users:
            # Get address information
            addresses = user.addresses.all()
            address_count = addresses.count()
            default_address = addresses.filter(is_default=True).first()
            default_addr_str = ""
            if default_address:
                default_addr_str = f"{default_address.address_line1}, {default_address.city}, {default_address.pincode}"
            
            writer.writerow([
                user.id,
                user.username,
                user.email,
                user.first_name,
                user.last_name,
                user.phone_number or '',
                user.is_active,
                user.is_staff,
                user.is_superuser,
                user.date_joined.strftime('%Y-%m-%d %H:%M:%S') if user.date_joined else '',
                user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '',
                address_count,
                default_addr_str
            ])
        
        messages.success(request, f'Successfully exported {users.count()} users to CSV.')
        return response


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Custom Address admin"""
    list_display = ('user', 'label', 'city', 'pincode', 'is_default', 'created_at')
    list_filter = ('is_default', 'city', 'state', 'country', 'created_at')
    search_fields = ('user__username', 'user__email', 'address_line1', 'city', 'pincode')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Address Details', {
            'fields': ('label', 'address_line1', 'address_line2', 'city', 'state', 'country', 'pincode')
        }),
        ('Location Data', {
            'fields': ('latitude', 'longitude', 'is_default'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
