from django.contrib import admin
from .models import Deal, Transaction, Dispute


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ['slug', 'item_description', 'amount', 'status', 'seller', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['slug', 'item_description', 'seller__username']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'deal', 'tx_type', 'status', 'amount', 'created_at']
    list_filter = ['tx_type', 'status']


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ['id', 'deal', 'status', 'created_at', 'resolved_at']
    list_filter = ['status']
