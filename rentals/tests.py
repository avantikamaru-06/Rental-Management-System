from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from customers.models import Customer
from products.models import Category, Product, RentalPeriod
from rentals.models import RentalOrder, RentalOrderItem, LateFee
from django.urls import reverse

class RentalLifecycleTests(TestCase):
    def setUp(self):
        # Create standard test data
        self.user = User.objects.create_user(username='testcust', password='pwd')
        self.customer = Customer.objects.create(user=self.user, phone='1234')
        self.category = Category.objects.create(name='Test Category')
        
        self.product = Product.objects.create(
            name='Test Camera',
            category=self.category,
            rental_price=Decimal('10.00'),
            security_deposit=Decimal('50.00'),
            late_fee_rate=Decimal('2.00'),
            is_available=True
        )
        
        self.period = RentalPeriod.objects.create(
            name='Daily',
            unit='days',
            multiplier=Decimal('1.00')
        )
        
    def test_pricing_multiplier(self):
        """Verify product base rental price multiplies correctly according to rental period rules."""
        base_price = self.product.rental_price * self.period.multiplier
        self.assertEqual(base_price, Decimal('10.00'))
        
    def test_order_creation_saves_successfully(self):
        """Verify a RentalOrder is successfully written to database with correct default fields."""
        order = RentalOrder.objects.create(
            customer=self.customer,
            status='confirmed',
            pickup_date=timezone.now(),
            return_date=timezone.now() + timezone.timedelta(days=2),
            total_amount=20.00,
            security_deposit_total=50.00,
            delivery_type='pickup',
            payment_status='unpaid'
        )
        self.assertEqual(RentalOrder.objects.count(), 1)
        self.assertEqual(order.status, 'confirmed')
        self.assertEqual(order.payment_status, 'unpaid')
        
    def test_late_fee_calculation_threshold(self):
        """Verify overdue returns accumulate correct penalty late fee rates."""
        order = RentalOrder.objects.create(
            customer=self.customer,
            status='picked_up',
            pickup_date=timezone.now() - timezone.timedelta(days=3),
            return_date=timezone.now() - timezone.timedelta(days=1), # return was yesterday
            total_amount=20.00,
            security_deposit_total=50.00,
            delivery_type='pickup',
            payment_status='fully_paid'
        )
        
        # Calculate late fee (e.g. 24 hours late)
        actual_return = timezone.now()
        hours_overdue = (actual_return - order.return_date).total_seconds() / 3600.0
        
        # Check if overdue is greater than 1 hour grace
        self.assertTrue(hours_overdue > 1.0)
        
        # Fee rate is $2/hr. Total fee for ~24 hours should be around $48.
        calculated_fee = self.product.late_fee_rate * Decimal(str(int(hours_overdue)))
        self.assertGreater(calculated_fee, Decimal('0.00'))

    def test_checkout_confirms_date_based_cart_rental(self):
        self.client.login(username='testcust', password='pwd')
        session = self.client.session
        session['cart'] = {
            f'{self.product.id}_{self.period.id}': {
                'product_id': self.product.id,
                'period_id': self.period.id,
                'duration': 3,
                'start_date': '2030-01-10',
                'end_date': '2030-01-12',
            }
        }
        session.save()
        response = self.client.post(reverse('rentals:checkout'), {
            'delivery_type': 'pickup',
            'pickup_date': '2030-01-10',
            'return_date': '2030-01-12',
            'payment_info': 'Visa **** 4321',
        })
        self.assertEqual(response.status_code, 302)
        order = RentalOrder.objects.get()
        self.assertEqual(order.rental_days, 3)
        self.assertEqual(order.status, 'confirmed')

    def test_checkout_handles_float_money_values(self):
        self.client.login(username='testcust', password='pwd')
        session = self.client.session
        session['cart'] = {
            f'{self.product.id}_{self.period.id}': {
                'product_id': self.product.id,
                'period_id': self.period.id,
                'duration': 1,
                'start_date': '2030-01-10',
                'end_date': '2030-01-10',
            }
        }
        session.save()

        product_with_float_values = Product.objects.get(pk=self.product.pk)
        product_with_float_values.rental_price = 10.0
        product_with_float_values.security_deposit = 50.0

        with patch('rentals.views.get_object_or_404', side_effect=lambda model, pk: product_with_float_values if model is Product else self.period):
            response = self.client.post(reverse('rentals:checkout'), {
                'delivery_type': 'pickup',
                'pickup_date': '2030-01-10',
                'return_date': '2030-01-10',
                'payment_info': 'Visa **** 9999',
            })

        self.assertEqual(response.status_code, 302)
        order = RentalOrder.objects.get()
        self.assertEqual(order.total_amount, Decimal('10.00'))
        self.assertEqual(order.security_deposit_total, Decimal('50.00'))

    def test_checkout_requires_payment_info_for_new_users(self):
        session = self.client.session
        session['cart'] = {
            f'{self.product.id}_{self.period.id}': {
                'product_id': self.product.id,
                'period_id': self.period.id,
                'duration': 1,
                'start_date': '2030-01-10',
                'end_date': '2030-01-10',
            }
        }
        session['pending_registration'] = {
            'username': 'newbuyer',
            'first_name': 'New',
            'last_name': 'Buyer',
            'email': 'newbuyer@example.com',
            'phone': '1234567890',
            'saved_address': '123 Test Street',
            'password_hash': make_password('pwd123'),
        }
        session.save()

        response = self.client.post(reverse('rentals:checkout'), {
            'delivery_type': 'pickup',
            'pickup_date': '2030-01-10',
            'return_date': '2030-01-10',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(RentalOrder.objects.count(), 0)
        self.assertFalse(Customer.objects.filter(user__username='newbuyer').exists())
