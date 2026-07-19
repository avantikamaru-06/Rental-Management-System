from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Quotation, QuotationItem
from .forms import QuotationForm, QuotationItemForm
from customers.models import Customer
from products.models import Product, RentalPeriod
from rentals.models import RentalOrder, RentalOrderItem, Pickup, Return, SecurityDeposit
from payments.models import Invoice, Payment
from notifications.models import Notification
from django.db import transaction
from decimal import Decimal
from rentals.utils import to_decimal, calculate_grand_total

@login_required
def quotation_list(request):
    is_admin = request.user.is_staff or request.user.is_superuser
    if is_admin:
        quotations = Quotation.objects.all().order_by('-id')
    else:
        # Ensure customer profile exists
        try:
            customer = request.user.customer_profile
            quotations = Quotation.objects.filter(customer=customer).order_by('-id')
        except Customer.DoesNotExist:
            quotations = Quotation.objects.none()
            
    return render(request, 'quotation/quotation_list.html', {
        'quotations': quotations,
        'is_admin': is_admin
    })

@login_required
def quotation_detail(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    is_admin = request.user.is_staff or request.user.is_superuser
    
    # Check permissions
    if not is_admin and quotation.customer.user != request.user:
        messages.error(request, "Access denied.")
        return redirect('quotation:quotation_list')
        
    items = quotation.items.all()
    
    # Handle adding item to quote (only in draft)
    item_form = None
    if quotation.status == 'draft':
        if request.method == 'POST' and 'add_item' in request.POST:
            item_form = QuotationItemForm(request.POST)
            if item_form.is_valid():
                item = item_form.save(commit=False)
                item.quotation = quotation
                
                # Apply template discounts if applicable
                discount = Decimal('1.00')
                if quotation.template_name == 'corporate':
                    discount = Decimal('0.85') # 15% discount
                elif quotation.template_name == 'special_event':
                    discount = Decimal('0.90') # 10% discount
                    
                base_price = to_decimal(item.product.rental_price) * to_decimal(item.rental_period.multiplier)
                item.price = base_price * discount
                item.save()
                
                # Update total
                quotation.total_amount = sum(to_decimal(x.price) * x.duration for x in quotation.items.all())
                quotation.save()
                
                messages.success(request, f"Added {item.product.name} to quotation.")
                return redirect('quotation:quotation_detail', pk=quotation.pk)
        else:
            item_form = QuotationItemForm()
            
    return render(request, 'quotation/quotation_detail.html', {
        'quotation': quotation,
        'items': items,
        'item_form': item_form,
        'is_admin': is_admin
    })

@login_required
def quotation_create(request):
    is_admin = request.user.is_staff or request.user.is_superuser
    
    if request.method == 'POST':
        form = QuotationForm(request.POST)
        if form.is_valid():
            quotation = form.save(commit=False)
            if not is_admin:
                quotation.customer = request.user.customer_profile
            quotation.status = 'draft'
            quotation.save()
            messages.success(request, "Quotation created. Now add items below.")
            return redirect('quotation:quotation_detail', pk=quotation.pk)
    else:
        if is_admin:
            form = QuotationForm()
        else:
            # For customer, auto-select them and hide selection in template
            try:
                customer = request.user.customer_profile
            except Customer.DoesNotExist:
                customer = Customer.objects.create(user=request.user)
            form = QuotationForm(initial={'customer': customer})
            
    return render(request, 'quotation/quotation_form.html', {
        'form': form,
        'is_admin': is_admin
    })

@login_required
def quotation_item_delete(request, pk):
    item = get_object_or_404(QuotationItem, pk=pk)
    quotation = item.quotation
    is_admin = request.user.is_staff or request.user.is_superuser
    
    if not is_admin and quotation.customer.user != request.user:
        messages.error(request, "Access denied.")
        return redirect('quotation:quotation_list')
        
    if quotation.status != 'draft':
        messages.error(request, "Cannot delete items from a locked quotation.")
        return redirect('quotation:quotation_detail', pk=quotation.pk)
        
    product_name = item.product.name
    item.delete()
    
    # Update total
    quotation.total_amount = sum(to_decimal(x.price) * x.duration for x in quotation.items.all())
    quotation.save()
    
    messages.success(request, f"Removed {product_name} from quotation.")
    return redirect('quotation:quotation_detail', pk=quotation.pk)

@login_required
def quotation_send(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    if not request.user.is_staff:
        messages.error(request, "Access denied.")
        return redirect('quotation:quotation_list')
        
    quotation.status = 'sent'
    quotation.save()
    
    # Create notification for customer
    Notification.objects.create(
        user=quotation.customer.user,
        title="Quotation Sent",
        message=f"Quotation #{quotation.id} has been prepared and sent for your review.",
        notification_type='rent_confirm'
    )
    
    messages.success(request, "Quotation status updated to 'Sent'. Customer notified.")
    return redirect('quotation:quotation_detail', pk=quotation.pk)

@login_required
def quotation_approve(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    
    if quotation.customer.user != request.user and not request.user.is_staff:
        messages.error(request, "Access denied.")
        return redirect('quotation:quotation_list')
        
    quotation.status = 'approved'
    quotation.save()
    
    messages.success(request, "Quotation approved. It can now be converted to an active Rental Order.")
    return redirect('quotation:quotation_detail', pk=quotation.pk)

@login_required
def quotation_convert(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    
    if not request.user.is_staff:
        messages.error(request, "Access denied. Only Admins can convert quotations to orders.")
        return redirect('quotation:quotation_detail', pk=quotation.pk)
        
    if quotation.status != 'approved':
        messages.error(request, "Only approved quotations can be converted.")
        return redirect('quotation:quotation_detail', pk=quotation.pk)
        
    # Begin transaction
    try:
        with transaction.atomic():
            # Calculate total deposit
            deposit_total = sum(item.product.security_deposit for item in quotation.items.all())
            
            # Create RentalOrder
            order = RentalOrder.objects.create(
                customer=quotation.customer,
                status='confirmed',
                pickup_date=timezone.now() + timezone.timedelta(days=1),
                return_date=timezone.now() + timezone.timedelta(days=7), # default 6 days
                total_amount=quotation.total_amount,
                security_deposit_total=deposit_total,
                delivery_type='pickup',
                payment_status='unpaid'
            )
            
            # Create items
            for q_item in quotation.items.all():
                RentalOrderItem.objects.create(
                    order=order,
                    product=q_item.product,
                    rental_period=q_item.rental_period,
                    duration=q_item.duration,
                    price=q_item.price
                )
                
                # Make product unavailable
                p = q_item.product
                p.is_available = False
                p.save()
                
            # Create Pickup schedule
            Pickup.objects.create(
                order=order,
                scheduled_time=order.pickup_date
            )
            
            # Create Return schedule
            Return.objects.create(
                order=order,
                scheduled_time=order.return_date
            )
            
            # Create SecurityDeposit tracking record
            SecurityDeposit.objects.create(
                order=order,
                amount=deposit_total,
                status='collected' # assumed pre-authorized/collected upon confirmation
            )
            
            # Create Invoice
            Invoice.objects.create(
                order=order,
                invoice_number=f"INV-QT-{order.id}-{uuid_num()}",
                total_amount=calculate_grand_total(order.total_amount, deposit_total),
                is_paid=False
            )
            
            # Update Quotation
            quotation.status = 'converted'
            quotation.save()
            
            # Create Notification
            Notification.objects.create(
                user=order.customer.user,
                title="Rental Order Created",
                message=f"Quotation #{quotation.id} converted successfully to Order #{order.id}.",
                notification_type='rent_confirm'
            )
            
            messages.success(request, f"Quotation converted to Order #{order.id} successfully!")
            return redirect('rentals:order_detail', pk=order.pk)
            
    except Exception as e:
        messages.error(request, f"Error converting quotation: {str(e)}")
        return redirect('quotation:quotation_detail', pk=quotation.pk)

def uuid_num():
    import random
    return random.randint(1000, 9999)
