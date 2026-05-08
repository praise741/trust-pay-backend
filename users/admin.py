from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, SellerProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'is_merchant', 'email_verified', 'phone_verified', 'is_staff']
    list_filter = ['is_merchant', 'email_verified', 'phone_verified', 'is_staff', 'is_superuser']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone', 'bank_name', 'bank_account_number', 'bank_code',
                      'is_merchant', 'email_verified', 'phone_verified', 'google_id')
        }),
    )


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'business_name', 'is_verified', 'total_deals', 'completed_deals', 'completion_rate']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['user__username', 'business_name', 'instagram_handle']
    readonly_fields = ['total_deals', 'completed_deals', 'created_at', 'updated_at']
