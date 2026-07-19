import uuid
from django.db import models
from django.contrib.auth.models import User
from customers.models import Customer
from products.models import Product, RentalPeriod

class RentalOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('quotation', 'Quotation'),
        ('confirmed', 'Confirmed / Reserved'),
        ('picked_up', 'Picked Up / Active'),
        ('returned', 'Returned / Completed'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    DELIVERY_CHOICES = [
        ('pickup', 'Customer Pickup'),
        ('delivery', 'Delivery to Address'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('deposit_paid', 'Deposit Paid Only'),
        ('fully_paid', 'Fully Paid'),
        ('refunded', 'Refunded'),
    ]

    ORDER_TYPE_CHOICES = [
        ('online', 'Online Order'),
        ('walk_in', 'Walk-in Order'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='rental_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES, default='online')
    order_date = models.DateTimeField(auto_now_add=True)
    pickup_date = models.DateTimeField(help_text="Scheduled pickup start date and time")
    return_date = models.DateTimeField(help_text="Scheduled return end date and time")
    rental_days = models.PositiveIntegerField(default=1, help_text="Number of rental days")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default='0.00')
    security_deposit_total = models.DecimalField(max_digits=10, decimal_places=2, default='0.00')
    delivery_type = models.CharField(max_length=15, choices=DELIVERY_CHOICES, default='pickup')
    shipping_address = models.TextField(blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True,
        related_name='created_rental_orders'
    )

    def __str__(self):
        return f"Order #{self.id} - {self.customer.display_name} ({self.get_status_display()})"

class RentalOrderItem(models.Model):
    order = models.ForeignKey(RentalOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    rental_period = models.ForeignKey(RentalPeriod, on_delete=models.PROTECT)
    duration = models.IntegerField(default=1, help_text="Number of units of the selected rental period")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Rental rate at checkout")

    def __str__(self):
        return f"{self.product.name} x {self.duration} {self.rental_period.unit} in Order #{self.order.id}"

class Pickup(models.Model):
    order = models.OneToOneField(RentalOrder, on_delete=models.CASCADE, related_name='pickup_details')
    scheduled_time = models.DateTimeField()
    actual_time = models.DateTimeField(blank=True, null=True)
    checklist_condition_checked = models.BooleanField(default=False, help_text="Verify product condition before pickup")
    checklist_id_verified = models.BooleanField(default=False, help_text="Verify customer identity document")
    checklist_agreement_signed = models.BooleanField(default=False, help_text="Customer signed rental agreement")
    qr_code_key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='confirmed_pickups')

    def __str__(self):
        return f"Pickup for Order #{self.order.id}"

class Return(models.Model):
    REPAIR_STATUS_CHOICES = [
        ('none', 'No Damages'),
        ('pending', 'Repair Assessment Pending'),
        ('repaired', 'Repaired & Settled'),
    ]
    order = models.OneToOneField(RentalOrder, on_delete=models.CASCADE, related_name='return_details')
    scheduled_time = models.DateTimeField()
    actual_time = models.DateTimeField(blank=True, null=True)
    checklist_damage_checked = models.BooleanField(default=False, help_text="Verify product for damages upon return")
    checklist_accessories_present = models.BooleanField(default=False, help_text="Verify all parts/accessories returned")
    damage_report = models.TextField(blank=True, null=True)
    missing_accessories = models.TextField(blank=True, null=True)
    late_fee_charged = models.DecimalField(max_digits=10, decimal_places=2, default='0.00')
    refunded_deposit = models.DecimalField(max_digits=10, decimal_places=2, default='0.00')
    repair_workflow_status = models.CharField(max_length=20, choices=REPAIR_STATUS_CHOICES, default='none')

    def __str__(self):
        return f"Return for Order #{self.order.id}"

class SecurityDeposit(models.Model):
    STATUS_CHOICES = [
        ('collected', 'Collected'),
        ('refunded', 'Fully Refunded'),
        ('deducted', 'Partially Deducted / Settled'),
    ]
    order = models.ForeignKey(RentalOrder, on_delete=models.CASCADE, related_name='security_deposits')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='collected')
    collected_at = models.DateTimeField(auto_now_add=True)
    refunded_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Deposit of ${self.amount} for Order #{self.order.id} ({self.status})"

class LateFee(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Payment / Deduction'),
        ('deducted', 'Deducted from Deposit'),
        ('paid', 'Paid Separately'),
    ]
    order = models.ForeignKey(RentalOrder, on_delete=models.CASCADE, related_name='late_fees')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    units_overdue = models.IntegerField(help_text="Overdue count (e.g. days/hours depending on unit)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Late Fee ${self.amount} for Order #{self.order.id} ({self.status})"
