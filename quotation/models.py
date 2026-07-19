from django.db import models
from customers.models import Customer
from products.models import Product, RentalPeriod

class Quotation(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft / Created'),
        ('sent', 'Sent to Customer'),
        ('approved', 'Approved by Customer'),
        ('converted', 'Converted to Order'),
        ('cancelled', 'Cancelled'),
    ]
    TEMPLATE_CHOICES = [
        ('standard', 'Standard Rental Template'),
        ('corporate', 'Corporate Partner Deal'),
        ('special_event', 'Wedding & Special Event Deal'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='quotations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default='0.00')
    template_name = models.CharField(max_length=30, choices=TEMPLATE_CHOICES, default='standard')

    def __str__(self):
        return f"Quotation #{self.id} - {self.customer.user.username} ({self.get_status_display()})"

class QuotationItem(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rental_period = models.ForeignKey(RentalPeriod, on_delete=models.CASCADE)
    duration = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Quoted unit rate")

    def __str__(self):
        return f"{self.product.name} x {self.duration} in Quote #{self.quotation.id}"
