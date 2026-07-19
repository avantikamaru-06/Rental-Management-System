from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from customers.models import Customer


class RootRedirectTests(TestCase):
    def setUp(self):
        self.customer_user = User.objects.create_user(username='customer_test', password='pass1234')
        Customer.objects.create(user=self.customer_user)

    def test_authenticated_customer_root_redirects_to_dashboard(self):
        self.client.force_login(self.customer_user)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:customer_dashboard'))

    def test_anonymous_user_root_redirects_to_products(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('products:product_list'))
