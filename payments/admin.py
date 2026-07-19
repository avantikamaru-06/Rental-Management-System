from django.contrib import admin
from .models import Payment, Invoice

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'amount', 'payment_type', 'payment_method', 'date', 'status')
    list_filter = ('payment_type', 'payment_method', 'status')
    search_fields = ('order__id',)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'order', 'issue_date', 'total_amount', 'is_paid')
    list_filter = ('is_paid',)
    search_fields = ('invoice_number', 'order__id')
