import os
import django
import random
from decimal import Decimal
from django.utils import timezone

# Configure Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rental_system.settings')
django.setup()

from django.contrib.auth.models import User
from customers.models import Customer
from products.models import Category, Product, RentalPeriod, Pricelist
from rentals.utils import calculate_grand_total
from rentals.models import RentalOrder, RentalOrderItem, Pickup, Return, SecurityDeposit, LateFee
from payments.models import Payment, Invoice
from notifications.models import Notification

def seed():
    print("Starting data seeding...")

    # 1. Create Superuser (Admin)
    if not User.objects.filter(username='admin').exists():
        admin_user = User.objects.create_superuser('admin', 'admin@rentalpro.com', 'admin123')
        admin_user.first_name = "System"
        admin_user.last_name = "Administrator"
        admin_user.save()
        print("Admin user created (admin / admin123)")
    else:
        admin_user = User.objects.get(username='admin')

    # 2. Create Portal Customer and bulk demo customers
    if not User.objects.filter(username='customer').exists():
        cust_user = User.objects.create_user('customer', 'john@example.com', 'customer123')
        cust_user.first_name = "John"
        cust_user.last_name = "Doe"
        cust_user.save()
        customer = Customer.objects.create(
            user=cust_user,
            phone="+1-555-0199",
            saved_address="456 Elm St, Springfield, IL 62701",
            payment_info="Visa **** 4242"
        )
        print("Customer user created (customer / customer123)")
    else:
        customer = Customer.objects.get(user__username='customer')

    # 3. Create Rental Periods
    periods = [
        {'name': 'Hourly', 'unit': 'hours', 'multiplier': 0.10},
        {'name': 'Daily', 'unit': 'days', 'multiplier': 1.00},
        {'name': 'Weekly', 'unit': 'weeks', 'multiplier': 5.00},
        {'name': 'Monthly', 'unit': 'months', 'multiplier': 15.00},
    ]
    for p_data in periods:
        RentalPeriod.objects.get_or_create(
            name=p_data['name'],
            defaults={'unit': p_data['unit'], 'multiplier': p_data['multiplier']}
        )
    print("Rental Periods configured.")

    # 4. Create Pricelists
    pricelists = [
        {'name': 'Default Pricelist', 'discount_percentage': 0.00, 'is_active': True},
        {'name': 'Weekend Special Deal', 'discount_percentage': 10.00, 'is_active': True},
        {'name': 'Bulk Corporate Partner', 'discount_percentage': 20.00, 'is_active': True},
    ]
    for pl_data in pricelists:
        Pricelist.objects.get_or_create(
            name=pl_data['name'],
            defaults={'discount_percentage': pl_data['discount_percentage'], 'is_active': pl_data['is_active']}
        )
    print("Pricelists configured.")

    # 5. Create Categories
    categories = ['Camera Gear', 'Power Tools', 'Outdoor Equipment', 'Party Supplies']
    cat_objs = {}
    for cat_name in categories:
        cat, _ = Category.objects.get_or_create(name=cat_name, defaults={'description': f"High-quality {cat_name.lower()} for rent."})
        cat_objs[cat_name] = cat
    print("Categories configured.")

    # 6. Create Products
    products_data = [
        {
            'name': 'Sony a7R V Mirrorless Camera',
            'category': cat_objs['Camera Gear'],
            'brand': 'Sony',
            'manufacturer': 'Sony Corp',
            'color': 'Black',
            'size': 'Standard Body',
            'description': '61MP full-frame mirrorless camera with advanced AI autofocus.',
            'rental_price': 80.00,
            'security_deposit': 300.00,
            'late_fee_rate': 15.00
        },
        {
            'name': 'Bosch SDS-Max Rotary Hammer',
            'category': cat_objs['Power Tools'],
            'brand': 'Bosch',
            'manufacturer': 'Bosch Power Tools',
            'color': 'Blue/Black',
            'size': 'Heavy Duty',
            'description': 'High-performance rotary hammer for concrete drilling and chiseling.',
            'rental_price': 45.00,
            'security_deposit': 150.00,
            'late_fee_rate': 10.00
        },
        {
            'name': '4-Person Geodesic Camping Tent',
            'category': cat_objs['Outdoor Equipment'],
            'brand': 'Coleman',
            'manufacturer': 'Coleman Co.',
            'color': 'Green/Orange',
            'size': '4-Person',
            'description': 'Weather-resistant geodesic tent with rainfly and dual entrances.',
            'rental_price': 25.00,
            'security_deposit': 80.00,
            'late_fee_rate': 5.00
        },
        {
            'name': 'JBL PartyBox 310 Speaker',
            'category': cat_objs['Party Supplies'],
            'brand': 'JBL',
            'manufacturer': 'Harman International',
            'color': 'Black with RGB',
            'size': 'Portable Large',
            'description': '240W loud portable party speaker with dynamic lights and built-in wheels.',
            'rental_price': 50.00,
            'security_deposit': 100.00,
            'late_fee_rate': 12.00
        }
    ]
    
    prod_objs = []
    for prod_data in products_data:
        prod, _ = Product.objects.get_or_create(
            name=prod_data['name'],
            defaults={
                'category': prod_data['category'],
                'brand': prod_data['brand'],
                'manufacturer': prod_data['manufacturer'],
                'color': prod_data['color'],
                'size': prod_data['size'],
                'description': prod_data['description'],
                'rental_price': prod_data['rental_price'],
                'security_deposit': prod_data['security_deposit'],
                'late_fee_rate': prod_data['late_fee_rate'],
                'is_available': True
            }
        )
        prod_objs.append(prod)
    print("Products configured.")

    first_names = ['Aarav','Aisha','Anika','Arjun','Bhavya','Chaitanya','Dev','Diya','Esha','Farhan','Gaurav','Hritik','Ishaan','Jiya','Kavya','Krish','Maya','Neha','Nikhil','Ojas','Pooja','Pranav','Riya','Rohan','Saanvi','Sahil','Sara','Shivam','Siya','Tanvi','Tejas','Uday','Uma','Vansh','Ved','Yash','Zara','Aditi','Aman','Anaya','Arushi','Ira','Kunal','Meera','Naina','Parth','Ritvik','Sakshi','Tara']
    last_names = ['Sharma','Patel','Singh','Kumar','Mehta','Verma','Kapoor','Gupta','Reddy','Rao','Joshi','Malhotra','Mishra','Iyer','Jain','Bhatia','Chauhan','Das','Nair','Saxena']
    payment_cards = ['Visa **** 4242','Mastercard **** 5532','Amex **** 8876','Visa **** 3344','Mastercard **** 7788']
    daily_period = RentalPeriod.objects.get(name='Daily')
    sample_product = prod_objs[0]

    for index in range(1, 51):
        username = f'cust{index}'
        if User.objects.filter(username=username).exists():
            continue
        user = User.objects.create_user(username=username, email=f'{username}@example.com', password='customer123')
        first_name = first_names[(index - 1) % len(first_names)]
        last_name = last_names[(index - 1) % len(last_names)]
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        customer_profile = Customer.objects.create(
            user=user,
            phone=f'+1-555-{1000 + index}',
            saved_address=f'{index} Demo Street, Test City {index % 10}',
            payment_info=payment_cards[(index - 1) % len(payment_cards)]
        )

        if index % 3 == 0:
            order = RentalOrder.objects.create(
                customer=customer_profile,
                status='confirmed',
                order_date=timezone.now() - timezone.timedelta(days=index),
                pickup_date=timezone.now() - timezone.timedelta(days=index - 1),
                return_date=timezone.now() + timezone.timedelta(days=2),
                total_amount=Decimal('25.00') + Decimal(index % 5),
                security_deposit_total=Decimal('50.00'),
                delivery_type='pickup',
                payment_status='fully_paid'
            )
            RentalOrderItem.objects.create(order=order, product=sample_product, rental_period=daily_period, duration=1, price=Decimal('25.00'))
            Payment.objects.create(order=order, amount=order.total_amount, payment_type='rental', status='success')
            Payment.objects.create(order=order, amount=order.security_deposit_total, payment_type='deposit', status='success')
            Invoice.objects.create(order=order, invoice_number=f'INV-{order.id}-{index:02d}', total_amount=calculate_grand_total(order.total_amount, order.security_deposit_total), is_paid=True)
    print("50 demo customers created with profile and payment details.")

    # 7. Create Seed Historical Transactions (for Dashboard Chart & reports population)
    now = timezone.now()
    daily_period = RentalPeriod.objects.get(name='Daily')
    customers = list(Customer.objects.exclude(user__username='admin').exclude(user__username='customer').select_related('user'))

    for month_offset in range(0, 6):
        for order_index in range(0, 8):
            order_time = now - timezone.timedelta(days=30 * month_offset + order_index * 4)
            p_date = order_time + timezone.timedelta(days=1)
            r_date = p_date + timezone.timedelta(days=3)
            customer = customers[(month_offset + order_index) % len(customers)] if customers else customer

            status = 'returned' if month_offset > 2 else 'picked_up'
            payment_status = 'refunded' if status == 'returned' else 'fully_paid'
            prod = prod_objs[(month_offset + order_index) % len(prod_objs)]
            rental_days = 3 if order_index % 2 == 0 else 2
            rental_total = prod.rental_price * rental_days
            deposit_total = prod.security_deposit

            order = RentalOrder.objects.create(
                customer=customer,
                status=status,
                order_date=order_time,
                pickup_date=p_date,
                return_date=r_date,
                total_amount=rental_total,
                security_deposit_total=deposit_total,
                delivery_type='pickup' if order_index % 2 == 0 else 'delivery',
                payment_status=payment_status
            )

            RentalOrderItem.objects.create(
                order=order,
                product=prod,
                rental_period=daily_period,
                duration=rental_days,
                price=prod.rental_price
            )

            Pickup.objects.create(
                order=order,
                scheduled_time=p_date,
                actual_time=p_date,
                checklist_condition_checked=True,
                checklist_id_verified=True,
                checklist_agreement_signed=True,
                confirmed_by=admin_user
            )

            if status == 'returned':
                actual_return = r_date + timezone.timedelta(hours=2)
                late_fee = prod.late_fee_rate * 2
                refund = deposit_total - late_fee

                Return.objects.create(
                    order=order,
                    scheduled_time=r_date,
                    actual_time=actual_return,
                    checklist_damage_checked=True,
                    checklist_accessories_present=True,
                    damage_report="Minor cosmetic wear detected.",
                    late_fee_charged=late_fee,
                    refunded_deposit=refund,
                    repair_workflow_status='none'
                )

                SecurityDeposit.objects.create(order=order, amount=deposit_total, status='deducted', collected_at=p_date, refunded_at=actual_return)
                LateFee.objects.create(order=order, amount=late_fee, units_overdue=2, status='deducted', created_at=actual_return)
                Payment.objects.create(order=order, amount=order.total_amount, payment_type='rental', date=order_time, status='success')
                Payment.objects.create(order=order, amount=order.security_deposit_total, payment_type='deposit', date=order_time, status='success')
                Payment.objects.create(order=order, amount=late_fee, payment_type='late_fee', date=actual_return, status='success')
                Payment.objects.create(order=order, amount=refund, payment_type='refund', date=actual_return, status='success')
            else:
                Return.objects.create(order=order, scheduled_time=r_date)
                SecurityDeposit.objects.create(order=order, amount=deposit_total, status='collected', collected_at=p_date)
                Payment.objects.create(order=order, amount=order.total_amount, payment_type='rental', date=order_time, status='success')
                Payment.objects.create(order=order, amount=order.security_deposit_total, payment_type='deposit', date=order_time, status='success')

            Invoice.objects.create(
                order=order,
                invoice_number=f"INV-SEED-{order.id}",
                issue_date=order_time,
                total_amount=calculate_grand_total(order.total_amount, order.security_deposit_total),
                is_paid=True
            )

            if status != 'returned':
                prod.is_available = False
                prod.save()

    print("Historical transaction seed completed.")
    print("Database seeding successfully finished.")

if __name__ == '__main__':
    seed()
