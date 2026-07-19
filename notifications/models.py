from django.db import models
from django.contrib.auth.models import User

class Notification(models.Model):
    TYPE_CHOICES = [
        ('rent_confirm', 'Rent Confirmation'),
        ('pickup_remind', 'Pickup Reminder'),
        ('return_remind', 'Return Reminder'),
        ('late_alert', 'Late Return Alert'),
        ('pay_success', 'Payment Success'),
        ('deposit_refund', 'Deposit Refund'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title} ({self.get_notification_type_display()})"
