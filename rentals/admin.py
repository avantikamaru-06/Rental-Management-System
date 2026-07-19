from django.contrib import admin
from .models import RentalOrder, RentalOrderItem, Pickup, Return, SecurityDeposit, LateFee

class RentalOrderItemInline(admin.TabularInline):
    model = RentalOrderItem
    extra = 0

@admin.register(RentalOrder)
class RentalOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'status', 'order_date', 'pickup_date', 'return_date', 'total_amount', 'payment_status')
    list_filter = ('status', 'payment_status', 'delivery_type')
    search_fields = ('customer__user__username', 'customer__user__first_name', 'customer__user__last_name', 'id')
    inlines = [RentalOrderItemInline]

@admin.register(RentalOrderItem)
class RentalOrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'rental_period', 'duration', 'price')
    list_filter = ('rental_period',)
    search_fields = ('product__name', 'order__id')

@admin.register(Pickup)
class PickupAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'scheduled_time', 'actual_time', 'checklist_condition_checked', 'checklist_id_verified', 'checklist_agreement_signed', 'confirmed_by')
    list_filter = ('checklist_condition_checked', 'checklist_id_verified', 'checklist_agreement_signed')
    search_fields = ('order__id', 'confirmed_by__username')

@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'scheduled_time', 'actual_time', 'checklist_damage_checked', 'checklist_accessories_present', 'late_fee_charged', 'refunded_deposit', 'repair_workflow_status')
    list_filter = ('checklist_damage_checked', 'checklist_accessories_present', 'repair_workflow_status')
    search_fields = ('order__id',)

@admin.register(SecurityDeposit)
class SecurityDepositAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'amount', 'status', 'collected_at', 'refunded_at')
    list_filter = ('status',)
    search_fields = ('order__id',)

@admin.register(LateFee)
class LateFeeAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'amount', 'units_overdue', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('order__id',)
