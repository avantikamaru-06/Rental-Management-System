from django import forms
from .models import Product, Category, RentalPeriod, Pricelist

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'category', 'brand', 'manufacturer', 'color', 'size', 
            'description', 'rental_price', 'security_deposit', 'late_fee_rate', 
            'image', 'is_available'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'size': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'rental_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'security_deposit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'late_fee_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
