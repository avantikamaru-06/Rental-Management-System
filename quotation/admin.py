from django.contrib import admin
from .models import Quotation, QuotationItem

class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 0

@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'status', 'created_at', 'total_amount', 'template_name')
    list_filter = ('status', 'template_name')
    search_fields = ('customer__user__username', 'id')
    inlines = [QuotationItemInline]

@admin.register(QuotationItem)
class QuotationItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'quotation', 'product', 'rental_period', 'duration', 'price')
    search_fields = ('product__name', 'quotation__id')
