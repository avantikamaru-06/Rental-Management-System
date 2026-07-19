from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.CharField(max_length=100, blank=True, null=True)
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    size = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    rental_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Base rental price per day")
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, help_text="Refundable deposit amount")
    late_fee_rate = models.DecimalField(max_digits=10, decimal_places=2, help_text="Late fee rate charged per unit time")
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class RentalPeriod(models.Model):
    UNIT_CHOICES = [
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
    ]
    name = models.CharField(max_length=50, unique=True, help_text="e.g. Hourly, Daily, Weekly, Monthly")
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='days')
    multiplier = models.DecimalField(max_digits=5, decimal_places=2, default='1.00', help_text="Price multiplier factor relative to base daily price")

    def __str__(self):
        return f"{self.name} ({self.unit} x {self.multiplier})"

class Pricelist(models.Model):
    name = models.CharField(max_length=100, unique=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default='0.00', help_text="Percentage discount applied to orders")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.discount_percentage}% Off)"
