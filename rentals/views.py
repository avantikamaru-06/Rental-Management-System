import uuid
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q
from products.models import Product, RentalPeriod, Pricelist
from customers.models import Customer
from payments.models import Payment, Invoice
from notifications.models import Notification
from .models import RentalOrder, RentalOrderItem, Pickup, Return, SecurityDeposit, LateFee
from django.db import transaction
from django.contrib.auth.models import User
from accounts.permissions import is_admin, is_salesperson, is_staff_member, is_customer
from .utils import calculate_rental_days, calculate_rental_price, calculate_grand_total, parse_date_input, is_product_available, get_unavailable_message, to_decimal

# ---------------- CART SYSTEM ----------------

def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_rental = Decimal('0.00')
    total_deposit = Decimal('0.00')
    
    for item_key, item_data in cart.items():
        # item_key is "product_id_period_id"
        product = get_object_or_404(Product, pk=item_data['product_id'])
        period = get_object_or_404(RentalPeriod, pk=item_data['period_id'])
        start_date = parse_date_input(item_data.get('start_date'))
        end_date = parse_date_input(item_data.get('end_date'))
        duration = calculate_rental_days(start_date, end_date) if start_date and end_date else int(item_data['duration'])
        
        # Calculate price based on period multiplier
        base_price = to_decimal(product.rental_price) if start_date and end_date else to_decimal(product.rental_price) * to_decimal(period.multiplier)
        item_price = base_price * duration
        item_deposit = to_decimal(product.security_deposit)
        
        total_rental += item_price
        total_deposit += item_deposit
        
        cart_items.append({
            'key': item_key,
            'product': product,
            'period': period,
            'duration': duration,
            'price_per_unit': base_price,
            'total_price': item_price,
            'deposit': item_deposit,
            'start_date': start_date,
            'end_date': end_date,
        })
        
    grand_total = calculate_grand_total(total_rental, total_deposit)
    
    return render(request, 'rentals/cart.html', {
        'cart_items': cart_items,
        'total_rental': total_rental,
        'total_deposit': total_deposit,
        'grand_total': grand_total
    })

def cart_add(request, product_id):
    if request.method == 'POST':
        period_id = request.POST.get('period')
        start_date = parse_date_input(request.POST.get('start_date'))
        end_date = parse_date_input(request.POST.get('end_date'))
        
        if not period_id:
            messages.error(request, "Please select a rental period.")
            return redirect('products:product_detail', pk=product_id)
        if not start_date or not end_date or end_date.date() < start_date.date():
            messages.error(request, "Please select valid start and end dates.")
            return redirect('products:product_detail', pk=product_id)
        if not is_product_available(product_id, start_date, end_date):
            messages.error(request, get_unavailable_message())
            return redirect('products:product_detail', pk=product_id)
            
        cart = request.session.get('cart', {})
        item_key = f"{product_id}_{period_id}"
        
        cart[item_key] = {
            'product_id': product_id,
            'period_id': period_id,
            'duration': calculate_rental_days(start_date, end_date),
            'start_date': request.POST.get('start_date'),
            'end_date': request.POST.get('end_date'),
        }
        
        request.session['cart'] = cart
        messages.success(request, "Product added to cart.")
    return redirect('rentals:cart')

def cart_remove(request, item_key):
    cart = request.session.get('cart', {})
    if item_key in cart:
        del cart[item_key]
        request.session['cart'] = cart
        messages.success(request, "Item removed from cart.")
    return redirect('rentals:cart')

def cart_clear(request):
    request.session['cart'] = {}
    messages.success(request, "Cart cleared.")
    return redirect('rentals:cart')

# ---------------- CHECKOUT & ORDERS ----------------

def checkout_view(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('products:product_list')

    # A single rental order has one pickup and return schedule. Keep all cart
    # items aligned to the dates selected when the first item was added.
    first_cart_item = next(iter(cart.values()))
    cart_start_date = first_cart_item.get('start_date')
    cart_end_date = first_cart_item.get('end_date')
        
    # Existing customers retain the normal flow. New registrations are staged
    # in session and persisted only after the simulated payment succeeds.
    customer = getattr(request.user, 'customer_profile', None) if request.user.is_authenticated else None
    pending_registration = request.session.get('pending_registration')
    if not customer and not pending_registration:
        messages.error(request, "Please register or sign in before checkout.")
        return redirect('accounts:register')
        
    cart_items = []
    total_rental = Decimal('0.00')
    total_deposit = Decimal('0.00')
    
    for item_key, item_data in cart.items():
        product = get_object_or_404(Product, pk=item_data['product_id'])
        period = get_object_or_404(RentalPeriod, pk=item_data['period_id'])
        duration = int(item_data['duration'])
        base_price = to_decimal(product.rental_price) * to_decimal(period.multiplier)
        item_price = base_price * duration
        item_deposit = to_decimal(product.security_deposit)
        
        total_rental += item_price
        total_deposit += item_deposit
        
        cart_items.append({
            'product': product,
            'period': period,
            'duration': duration,
            'total_price': item_price,
            'deposit': item_deposit
        })
        
    grand_total = calculate_grand_total(total_rental, total_deposit)
    
    if request.method == 'POST':
        delivery_type = request.POST.get('delivery_type')
        shipping_address = request.POST.get('shipping_address', '')
        pickup_date_str = request.POST.get('pickup_date')
        return_date_str = request.POST.get('return_date')
        payment_info = (request.POST.get('payment_info') or '').strip()
        
        if not pickup_date_str or not return_date_str:
            messages.error(request, "Please specify both pickup and return dates.")
            return redirect('rentals:checkout')

        if not payment_info:
            messages.error(request, "Please enter simulated payment details before confirming checkout.")
            return redirect('rentals:checkout')
            
        try:
            pickup_date = parse_date_input(pickup_date_str)
            return_date = parse_date_input(return_date_str)
        except (ValueError, TypeError):
            messages.error(request, "Invalid dates provided.")
            return redirect('rentals:checkout')
            
        if not pickup_date or not return_date or return_date.date() < pickup_date.date():
            messages.error(request, "End date cannot be before start date.")
            return redirect('rentals:checkout')
        rental_days = calculate_rental_days(pickup_date, return_date)
        recalculated_rental = sum(calculate_rental_price(item['product'].rental_price, rental_days) for item in cart_items)
        grand_total = calculate_grand_total(recalculated_rental, total_deposit)
        for item in cart_items:
            if not is_product_available(item['product'].id, pickup_date, return_date):
                messages.error(request, get_unavailable_message())
                return redirect('rentals:checkout')
            
        # Create order within transaction
        try:
            with transaction.atomic():
                if customer is None:
                    pending = pending_registration
                    if User.objects.filter(username=pending['username']).exists():
                        messages.error(request, "That username is already in use. Please sign in or register again.")
                        return redirect('accounts:register')
                    user = User.objects.create(
                        username=pending['username'], password=pending['password_hash'],
                        first_name=pending.get('first_name', ''), last_name=pending.get('last_name', ''),
                        email=pending.get('email', ''),
                    )
                    customer = Customer.objects.create(
                        user=user,
                        phone=pending.get('phone'),
                        saved_address=pending.get('saved_address'),
                        payment_info=payment_info,
                    )
                    request.session['pending_registration'] = {
                        **pending,
                        'payment_info': payment_info,
                    }
                else:
                    user = request.user
                    if payment_info:
                        customer.payment_info = payment_info
                        customer.save(update_fields=['payment_info'])
                order = RentalOrder.objects.create(
                    customer=customer,
                    status='confirmed',
                    order_type='online',
                    pickup_date=pickup_date,
                    return_date=return_date,
                    rental_days=rental_days,
                    total_amount=recalculated_rental,
                    security_deposit_total=total_deposit,
                    delivery_type=delivery_type,
                    shipping_address=shipping_address if delivery_type == 'delivery' else '',
                    payment_status='fully_paid', # mock credit card checkout pays both
                    created_by=user if is_staff_member(user) else None,
                )
                
                for item in cart_items:
                    RentalOrderItem.objects.create(
                        order=order,
                        product=item['product'],
                        rental_period=item['period'],
                        duration=rental_days,
                        price=item['product'].rental_price
                    )
                    # Mark product unavailable
                    p = item['product']
                    p.is_available = False
                    p.save()
                    
                # Create Pickup & Return Schedules
                Pickup.objects.create(order=order, scheduled_time=pickup_date)
                Return.objects.create(order=order, scheduled_time=return_date)
                
                # Create SecurityDeposit tracking record
                SecurityDeposit.objects.create(
                    order=order,
                    amount=total_deposit,
                    status='collected'
                )
                
                # Create Invoice
                invoice_num = f"INV-{order.id}-{uuid.uuid4().hex[:6].upper()}"
                Invoice.objects.create(
                    order=order,
                    invoice_number=invoice_num,
                    total_amount=calculate_grand_total(order.total_amount, order.security_deposit_total),
                    is_paid=True
                )
                
                # Create payments
                Payment.objects.create(
                    order=order,
                    amount=order.total_amount,
                    payment_type='rental',
                    payment_method='card',
                    status='success'
                )
                Payment.objects.create(
                    order=order,
                    amount=order.security_deposit_total,
                    payment_type='deposit',
                    payment_method='card',
                    status='success'
                )
                
                # Create Notifications
                Notification.objects.create(
                    user=user,
                    title="Order Placed Successfully",
                    message=f"Order #{order.id} for {len(cart_items)} item(s) has been placed and paid.",
                    notification_type='rent_confirm'
                )
                
                # Clear Cart
                request.session['cart'] = {}
                request.session.pop('pending_registration', None)
                if not request.user.is_authenticated:
                    from django.contrib.auth import login
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    login(request, user)
                
                messages.success(request, f"Order #{order.id} placed successfully!")
                return redirect('rentals:order_detail', pk=order.pk)
                
        except Exception as e:
            messages.error(request, f"Checkout failed: {str(e)}")
            return redirect('rentals:checkout')
            
    return render(request, 'rentals/checkout.html', {
        'cart_items': cart_items,
        'total_rental': total_rental,
        'total_deposit': total_deposit,
        'grand_total': grand_total,
        'daily_rate': sum(item['product'].rental_price for item in cart_items),
        'cart_start_date': cart_start_date,
        'cart_end_date': cart_end_date,
        'customer': customer
    })

@login_required
def order_list(request):
    is_admin_user = is_admin(request.user)
    is_staff_user = is_staff_member(request.user)
    if is_admin_user:
        orders = RentalOrder.objects.all().order_by('-id')
    elif is_salesperson(request.user):
        orders = RentalOrder.objects.filter(created_by=request.user).order_by('-id')
    else:
        try:
            customer = request.user.customer_profile
            orders = RentalOrder.objects.filter(customer=customer).order_by('-id')
        except Customer.DoesNotExist:
            orders = RentalOrder.objects.none()
            
    return render(request, 'rentals/order_list.html', {
        'orders': orders,
        'is_admin': is_staff_user
    })

@login_required
def order_detail(request, pk):
    order = get_object_or_404(RentalOrder, pk=pk)
    is_admin_user = is_admin(request.user)
    is_staff_user = is_staff_member(request.user)
    
    if not is_admin_user and not (is_salesperson(request.user) and order.created_by == request.user) and order.customer.user != request.user:
        messages.error(request, "Access denied.")
        return redirect('rentals:order_list')
        
    items = order.items.all()
    payments = order.payments.all()
    invoices = order.invoices.all()
    
    # Try fetching pickup & return details
    pickup = getattr(order, 'pickup_details', None)
    ret_detail = getattr(order, 'return_details', None)
    
    return render(request, 'rentals/order_detail.html', {
        'order': order,
        'items': items,
        'payments': payments,
        'invoices': invoices,
        'pickup': pickup,
        'return_detail': ret_detail,
        'is_admin': is_staff_user
    })


@login_required
@user_passes_test(is_staff_member)
def walk_in_order_create(request):
    """Create a paid walk-in rental without requiring a customer login."""
    products = Product.objects.filter(is_available=True).order_by('name')
    if request.method == 'POST':
        name = request.POST.get('customer_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        product = get_object_or_404(Product, pk=request.POST.get('product'))
        start = parse_date_input(request.POST.get('start_date'))
        end = parse_date_input(request.POST.get('end_date'))
        payment_method = request.POST.get('payment_method', 'cash')
        status = request.POST.get('status', 'confirmed')
        if not name or not start or not end or end.date() < start.date():
            messages.error(request, "Enter the customer details and valid rental dates.")
        elif not is_product_available(product.id, start, end):
            messages.error(request, get_unavailable_message())
        else:
            days = calculate_rental_days(start, end)
            rental_price = calculate_rental_price(product.rental_price, days)
            with transaction.atomic():
                customer = Customer.objects.create(walk_in_name=name, is_walk_in=True, phone=phone, saved_address=address)
                period = RentalPeriod.objects.filter(unit='days').first() or RentalPeriod.objects.first()
                if not period:
                    messages.error(request, "Create a rental period before making a rental.")
                    return redirect('rentals:walk_in_order_create')
                order = RentalOrder.objects.create(
                    customer=customer, order_type='walk_in', created_by=request.user, status=status,
                    pickup_date=start, return_date=end, rental_days=days, total_amount=rental_price,
                    security_deposit_total=product.security_deposit, payment_status='fully_paid',
                )
                RentalOrderItem.objects.create(order=order, product=product, rental_period=period, duration=days, price=product.rental_price)
                Pickup.objects.create(order=order, scheduled_time=start)
                Return.objects.create(order=order, scheduled_time=end)
                SecurityDeposit.objects.create(order=order, amount=product.security_deposit)
                Invoice.objects.create(order=order, invoice_number=f"INV-{order.id}-{uuid.uuid4().hex[:6].upper()}", total_amount=calculate_grand_total(rental_price, product.security_deposit), is_paid=True)
                Payment.objects.create(order=order, amount=rental_price, payment_type='rental', payment_method=payment_method, status='success')
                Payment.objects.create(order=order, amount=product.security_deposit, payment_type='deposit', payment_method=payment_method, status='success')
            messages.success(request, f"Walk-in rental #{order.id} saved successfully.")
            return redirect('rentals:order_detail', pk=order.pk)
    return render(request, 'rentals/walk_in_order_form.html', {'products': products})

def product_search_ajax(request):
    query = request.GET.get('q', '').strip()
    queryset = Product.objects.select_related('category').order_by('name')
    if query:
        numeric_query = None
        try:
            numeric_query = int(query)
        except ValueError:
            numeric_query = None

        queryset = queryset.filter(
            Q(name__icontains=query) |
            Q(brand__icontains=query) |
            Q(category__name__icontains=query) |
            (Q(pk=numeric_query) if numeric_query is not None else Q())
        )

    results = []
    for product in queryset[:50]:
        results.append({
            'id': product.pk,
            'text': f"{product.name} - {product.brand or 'No Brand'} ({product.category.name if product.category else 'Uncategorized'})",
            'name': product.name,
            'brand': product.brand or 'N/A',
            'category': product.category.name if product.category else 'Uncategorized',
            'price': format(product.rental_price, '.2f'),
            'deposit': format(product.security_deposit, '.2f'),
            'image_url': product.image.url if product.image else '',
            'stock': 1 if product.is_available else 0,
            'status': 'Available' if product.is_available else 'Unavailable',
        })

    return JsonResponse({'results': results})

# ---------------- PICKUP & RETURN WORKFLOWS ----------------

@login_required
@user_passes_test(is_staff_member)
def pickup_confirm(request, pk):
    order = get_object_or_404(RentalOrder, pk=pk)
    pickup = get_object_or_404(Pickup, order=order)
    
    if order.status != 'confirmed':
        messages.error(request, "Order is not in a states eligible for pickup.")
        return redirect('rentals:order_detail', pk=order.pk)
        
    if request.method == 'POST':
        cond_check = request.POST.get('cond_check') == 'on'
        id_check = request.POST.get('id_check') == 'on'
        sign_check = request.POST.get('sign_check') == 'on'
        
        if cond_check and id_check and sign_check:
            pickup.checklist_condition_checked = True
            pickup.checklist_id_verified = True
            pickup.checklist_agreement_signed = True
            pickup.actual_time = timezone.now()
            pickup.confirmed_by = request.user
            pickup.save()
            
            order.status = 'picked_up'
            order.save()
            
            # Customer Notification
            if order.customer.user:
                Notification.objects.create(
                    user=order.customer.user, title="Product Picked Up",
                    message=f"You have picked up the items for Order #{order.id} successfully.", notification_type='pickup_remind'
                )
            
            messages.success(request, f"Pickup confirmed for Order #{order.id}. Rental is now active.")
            return redirect('rentals:order_detail', pk=order.pk)
        else:
            messages.error(request, "All checklist items must be verified before confirming pickup.")
            
    return render(request, 'rentals/pickup_confirm.html', {
        'order': order,
        'pickup': pickup
    })

@login_required
@user_passes_test(is_staff_member)
def return_confirm(request, pk):
    order = get_object_or_404(RentalOrder, pk=pk)
    ret_detail = get_object_or_404(Return, order=order)
    
    if order.status != 'picked_up' and order.status != 'overdue':
        messages.error(request, "Order is not active, return cannot be processed.")
        return redirect('rentals:order_detail', pk=order.pk)
        
    actual_now = timezone.now()
    
    # Calculate Late Return Fee
    grace_hours = 1.0
    late_fee_amount = Decimal('0.00')
    hours_overdue = 0.0
    
    if actual_now > order.return_date:
        overdue_delta = actual_now - order.return_date
        hours_overdue = overdue_delta.total_seconds() / 3600.0
        
        if hours_overdue > grace_hours:
            # Calculate late fee
            # Loop order items, get product late fee rate. 
            # We calculate late fee per item per hour overdue
            for item in order.items.all():
                late_fee_amount += to_decimal(item.product.late_fee_rate) * int(hours_overdue)
                
    if request.method == 'POST':
        damage_check = request.POST.get('damage_check') == 'on'
        acc_check = request.POST.get('acc_check') == 'on'
        damage_report = request.POST.get('damage_report', '')
        missing_acc = request.POST.get('missing_accessories', '')
        repair_status = request.POST.get('repair_status', 'none')
        
        if damage_check and acc_check:
            # Begin atomic transaction
            try:
                with transaction.atomic():
                    # Deduct late fee from deposit, calculate refund
                    deposit_amount = to_decimal(order.security_deposit_total)
                    refund_amount = deposit_amount - late_fee_amount
                    
                    if refund_amount < 0:
                        refund_amount = Decimal('0.00')
                        
                    # Save Return Details
                    ret_detail.checklist_damage_checked = True
                    ret_detail.checklist_accessories_present = True
                    ret_detail.actual_time = actual_now
                    ret_detail.damage_report = damage_report
                    ret_detail.missing_accessories = missing_acc
                    ret_detail.late_fee_charged = late_fee_amount
                    ret_detail.refunded_deposit = refund_amount
                    ret_detail.repair_workflow_status = repair_status
                    ret_detail.save()
                    
                    # Update Order status
                    order.status = 'returned'
                    order.payment_status = 'refunded'
                    order.save()
                    
                    # Restock products
                    for item in order.items.all():
                        p = item.product
                        p.is_available = True
                        p.save()
                        
                    # Log LateFee record if charged
                    if late_fee_amount > 0:
                        LateFee.objects.create(
                            order=order,
                            amount=late_fee_amount,
                            units_overdue=int(hours_overdue),
                            status='deducted'
                        )
                        # Log deduction payment
                        Payment.objects.create(
                            order=order,
                            amount=late_fee_amount,
                            payment_type='late_fee',
                            payment_method='deposit_deduct',
                            status='success'
                        )
                        
                    # Settle SecurityDeposit record
                    sd = SecurityDeposit.objects.filter(order=order, status='collected').first()
                    if sd:
                        sd.status = 'deducted' if late_fee_amount > 0 else 'refunded'
                        sd.refunded_at = actual_now
                        sd.save()
                        
                    # Log refund payment
                    if refund_amount > 0:
                        Payment.objects.create(
                            order=order,
                            amount=refund_amount,
                            payment_type='refund',
                            payment_method='card', # assume card credit
                            status='success'
                        )
                        
                    # Customer Notification
                    if order.customer.user:
                        Notification.objects.create(
                            user=order.customer.user, title="Product Returned & Deposit Settled",
                            message=f"Return processed for Order #{order.id}. Late Fee: ${late_fee_amount}. Refund: ${refund_amount}.",
                            notification_type='return_remind'
                        )
                    
                    messages.success(request, f"Return processed successfully. Stock updated and deposit settled.")
                    return redirect('rentals:order_detail', pk=order.pk)
            except Exception as e:
                messages.error(request, f"Failed to process return: {str(e)}")
        else:
            messages.error(request, "Checklist items must be verified before confirming return.")
            
    return render(request, 'rentals/return_confirm.html', {
        'order': order,
        'return_detail': ret_detail,
        'late_fee_amount': late_fee_amount,
        'hours_overdue': int(hours_overdue),
        'actual_now': actual_now
    })
