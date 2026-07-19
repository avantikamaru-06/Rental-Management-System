from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'phone', 'saved_address', 'payment_info')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone')
