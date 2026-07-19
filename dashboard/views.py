from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from products.models import Product
from customers.models import Customer
from rentals.models import RentalOrder, SecurityDeposit, LateFee, Pickup, Return
from payments.models import Payment, Invoice
from notifications.models import Notification
from django.contrib import messages
from accounts.permissions import is_admin, is_salesperson

@login_required
def home_view(request):
    if is_admin(request.user):
        return redirect('dashboard:admin_dashboard')
    if is_salesperson(request.user):
        return redirect('dashboard:salesperson_dashboard')
    return redirect('dashboard:customer_dashboard')

@login_required
def admin_dashboard(request):
    if not is_admin(request.user):
        return redirect('dashboard:customer_dashboard')
        
    now = timezone.now()
    
    # Auto-detect overdue rentals
    overdue_orders = RentalOrder.objects.filter(return_date__lt=now, status='picked_up')
    for order in overdue_orders:
        order.status = 'overdue'
        order.save()
        # Log notification
        if order.customer.user:
            Notification.objects.get_or_create(
                user=order.customer.user,
                title="Rental Overdue Alert",
                message=f"Order #{order.id} is overdue. Please return the items to avoid additional fees.",
                notification_type='late_alert'
            )
        
    # KPIs
    total_products = Product.objects.count()
    available_products = Product.objects.filter(is_available=True).count()
    rented_products = Product.objects.filter(is_available=False).count()
    
    due_today_count = RentalOrder.objects.filter(
        return_date__date=now.date(), 
        status__in=['picked_up', 'overdue']
    ).count()
    
    total_customers = Customer.objects.count()
    
    # Revenue calculations
    revenue_agg = Payment.objects.filter(payment_type='rental', status='success').aggregate(Sum('amount'))
    total_revenue = revenue_agg['amount__sum'] or 0.0
    
    deposit_agg = SecurityDeposit.objects.filter(status='collected').aggregate(Sum('amount'))
    held_deposits = deposit_agg['amount__sum'] or 0.0
    
    late_agg = LateFee.objects.aggregate(Sum('amount'))
    late_fees_collected = late_agg['amount__sum'] or 0.0
    
    # Tables
    upcoming_pickups = RentalOrder.objects.filter(
        pickup_date__gt=now, 
        status='confirmed'
    ).order_by('pickup_date')[:5]
    
    upcoming_returns = RentalOrder.objects.filter(
        return_date__gt=now, 
        status='picked_up'
    ).order_by('return_date')[:5]
    
    overdue_rentals = RentalOrder.objects.filter(status='overdue')
    
    recent_rentals = RentalOrder.objects.all().order_by('-order_date')[:5]
    recent_payments = Payment.objects.all().order_by('-date')[:5]
    
    # Aggregated monthly revenue for Chart.js
    monthly_revenue = []
    # Since it is a student level app, we can just aggregate recent 6 months hardcoded or compute
    for i in range(1, 7):
        month_date = now - timezone.timedelta(days=30 * (6-i))
        month_payments = Payment.objects.filter(
            payment_type='rental', 
            status='success',
            date__year=month_date.year,
            date__month=month_date.month
        ).aggregate(Sum('amount'))
        monthly_revenue.append({
            'month': month_date.strftime('%B'),
            'amount': float(month_payments['amount__sum'] or 0.0)
        })
        
    return render(request, 'dashboard/admin_dashboard.html', {
        'total_products': total_products,
        'available_products': available_products,
        'rented_products': rented_products,
        'due_today_count': due_today_count,
        'total_customers': total_customers,
        'total_revenue': total_revenue,
        'held_deposits': held_deposits,
        'late_fees_collected': late_fees_collected,
        'upcoming_pickups': upcoming_pickups,
        'upcoming_returns': upcoming_returns,
        'overdue_rentals': overdue_rentals,
        'recent_rentals': recent_rentals,
        'recent_payments': recent_payments,
        'monthly_revenue': monthly_revenue,
        'total_salespersons': __import__('accounts.models', fromlist=['UserProfile']).UserProfile.objects.filter(role='salesperson').count(),
        'walk_in_rentals': RentalOrder.objects.filter(order_type='walk_in').count(),
        'online_rentals': RentalOrder.objects.filter(order_type='online').count(),
        'todays_revenue': Payment.objects.filter(date__date=now.date(), status='success', payment_type__in=['rental', 'late_fee']).aggregate(Sum('amount'))['amount__sum'] or 0,
        'pending_returns': RentalOrder.objects.filter(status__in=['picked_up', 'overdue']).count(),
        'top_salespeople': RentalOrder.objects.filter(created_by__profile__role='salesperson').values('created_by__username').annotate(total=__import__('django.db.models', fromlist=['Count']).Count('id')).order_by('-total')[:5],
    })


@login_required
def salesperson_dashboard(request):
    if not is_salesperson(request.user):
        return redirect('dashboard:home')
    today = timezone.now().date()
    orders = RentalOrder.objects.filter(created_by=request.user)
    return render(request, 'dashboard/salesperson_dashboard.html', {
        'today_rentals': orders.filter(order_date__date=today).count(),
        'today_collection': Payment.objects.filter(order__created_by=request.user, date__date=today, status='success').aggregate(Sum('amount'))['amount__sum'] or 0,
        'pending_returns': orders.filter(status__in=['picked_up', 'overdue']).count(),
        'customer_count': Customer.objects.filter(rental_orders__created_by=request.user).distinct().count(),
        'recent_orders': orders.order_by('-order_date')[:8],
    })

@login_required
def customer_dashboard(request):
    try:
        customer = request.user.customer_profile
    except Customer.DoesNotExist:
        customer = Customer.objects.create(user=request.user)
        
    orders = RentalOrder.objects.filter(customer=customer).order_by('-id')
    recent_orders = orders[:5]
    
    # Stats
    active_rentals = orders.filter(status='picked_up').count()
    overdue_rentals = orders.filter(status='overdue').count()
    
    spent_agg = Payment.objects.filter(
        order__customer=customer, 
        payment_type__in=['rental', 'late_fee'], 
        status='success'
    ).aggregate(Sum('amount'))
    total_spent = spent_agg['amount__sum'] or 0.0
    
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:5]
    
    return render(request, 'dashboard/customer_dashboard.html', {
        'customer': customer,
        'recent_orders': recent_orders,
        'active_rentals': active_rentals,
        'overdue_rentals': overdue_rentals,
        'total_spent': total_spent,
        'notifications': notifications
    })
