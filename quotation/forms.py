from django import forms
from .models import Quotation, QuotationItem
from customers.models import Customer
from products.models import Product, RentalPeriod

class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ['customer', 'template_name']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'template_name': forms.Select(attrs={'class': 'form-select'}),
        }

class QuotationItemForm(forms.ModelForm):
    class Meta:
        model = QuotationItem
        fields = ['product', 'rental_period', 'duration']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'rental_period': forms.Select(attrs={'class': 'form-select'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
