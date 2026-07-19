from django.contrib import admin
from .models import Category, Product, RentalPeriod, Pricelist

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'brand', 'rental_price', 'security_deposit', 'is_available')
    list_filter = ('category', 'is_available', 'brand')
    search_fields = ('name', 'brand', 'manufacturer', 'description')

@admin.register(RentalPeriod)
class RentalPeriodAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'unit', 'multiplier')
    list_filter = ('unit',)
    search_fields = ('name',)

@admin.register(Pricelist)
class PricelistAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'discount_percentage', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
