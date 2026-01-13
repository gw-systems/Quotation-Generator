from django.contrib import admin
from .models import Client, Quotation, QuotationItem, QuotationAudit


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Admin interface for Client model"""
    list_display = ('client_name', 'company_name', 'email', 'contact_number', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('client_name', 'company_name', 'email', 'contact_number')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Client Information', {
            'fields': ('client_name', 'company_name', 'email', 'contact_number', 'address')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class QuotationItemInline(admin.TabularInline):
    """Inline admin for QuotationItem"""
    model = QuotationItem
    extra = 1
    fields = ('item_description', 'unit_cost', 'quantity', 'total', 'order')
    readonly_fields = ('total',)
    ordering = ('order',)


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    """Admin interface for Quotation model"""
    list_display = ('quotation_number', 'client', 'date', 'status', 'grand_total', 'created_by', 'created_at')
    list_filter = ('status', 'date', 'created_at')
    search_fields = ('quotation_number', 'client__client_name', 'client__company_name')
    readonly_fields = ('quotation_number', 'date', 'subtotal', 'gst_amount', 'grand_total', 'validity_date', 'created_at', 'updated_at')
    inlines = [QuotationItemInline]
    
    fieldsets = (
        ('Quotation Details', {
            'fields': ('quotation_number', 'client', 'date', 'validity_period', 'validity_date', 'point_of_contact', 'status')
        }),
        ('Financial Summary', {
            'fields': ('subtotal', 'gst_amount', 'grand_total'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Set created_by when creating new quotation"""
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(QuotationItem)
class QuotationItemAdmin(admin.ModelAdmin):
    """Admin interface for QuotationItem model"""
    list_display = ('quotation', 'item_description', 'unit_cost', 'quantity', 'total', 'order')
    list_filter = ('item_description',)
    search_fields = ('quotation__quotation_number', 'item_description')
    readonly_fields = ('total', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Item Details', {
            'fields': ('quotation', 'item_description', 'unit_cost', 'quantity', 'total', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(QuotationAudit)
class QuotationAuditAdmin(admin.ModelAdmin):
    """Admin interface for QuotationAudit model"""
    list_display = ('quotation', 'action', 'user', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('quotation__quotation_number', 'user__username')
    readonly_fields = ('quotation', 'action', 'user', 'timestamp', 'changes', 'ip_address', 'additional_metadata')
    
    fieldsets = (
        ('Audit Information', {
            'fields': ('quotation', 'action', 'user', 'timestamp', 'ip_address')
        }),
        ('Details', {
            'fields': ('changes', 'additional_metadata'),
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent manual creation of audit logs"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of audit logs"""
        return False


# Customize User admin to emphasize email
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Unregister existing User admin
admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Enhanced User admin with email emphasis"""
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email'),
            'description': 'Email is required for users who create quotations.'
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
