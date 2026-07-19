from django.db import models
from django.contrib.auth.models import User


class Customer(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='customer_profile',
        null=True, blank=True
    )
    walk_in_name = models.CharField(max_length=200, blank=True, null=True)
    is_walk_in = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    saved_address = models.TextField(blank=True, null=True)
    payment_info = models.CharField(max_length=100, blank=True, null=True, help_text="Card details placeholder (e.g. Visa **** 1234)")

    @property
    def display_name(self):
        if self.user:
            name = f"{self.user.first_name} {self.user.last_name}".strip()
            return name or self.user.username
        return self.walk_in_name or f"Walk-in Customer #{self.pk}"

    @property
    def display_username(self):
        if self.user:
            return self.user.username
        return self.walk_in_name or f"Walk-in #{self.pk}"

    def __str__(self):
        return self.display_name
