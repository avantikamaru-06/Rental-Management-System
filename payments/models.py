from django.db import models
from rentals.models import RentalOrder

class Payment(models.Model):
    TYPE_CHOICES = [
        ('rental', 'Rental Charges'),
        ('deposit', 'Security Deposit'),
        ('late_fee', 'Late Return Fee'),
        ('refund', 'Security Deposit Refund'),
    ]
    METHOD_CHOICES = [
        ('card', 'Credit / Debit Card'),
        ('cash', 'Cash payment'),
        ('deposit_deduct', 'Deposit Deduction'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    order = models.ForeignKey(RentalOrder, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='card')
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='success')

    def __str__(self):
        return f"Payment #{self.id} - ${self.amount} ({self.get_payment_type_display()}) - {self.status}"

class Invoice(models.Model):
    order = models.ForeignKey(RentalOrder, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=50, unique=True)
    issue_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Invoice {self.invoice_number} - Order #{self.order.id} (${self.total_amount})"
