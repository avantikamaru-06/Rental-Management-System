from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count
from django.utils import timezone
from products.models import Product
from customers.models import Customer
from rentals.models import RentalOrder, SecurityDeposit, LateFee
from payments.models import Payment
from accounts.permissions import is_admin, is_salesperson

@login_required
def reports_home(request):
    if not (is_admin(request.user) or is_salesperson(request.user)):
        return redirect('dashboard:home')
    # 1. Rental Report
    rentals = RentalOrder.objects.all().order_by('-order_date') if is_admin(request.user) else RentalOrder.objects.filter(created_by=request.user).order_by('-order_date')
    
    # 2. Customer Report
    customers = Customer.objects.annotate(
        order_count=Count('rental_orders'),
        total_spent=Sum('rental_orders__total_amount')
    ).order_by('-total_spent')
    if not is_admin(request.user):
        customers = customers.filter(rental_orders__created_by=request.user).distinct()
    
    # 3. Revenue Report
    payment_scope = Payment.objects.filter(status='success') if is_admin(request.user) else Payment.objects.filter(status='success', order__created_by=request.user)
    revenue_rental = payment_scope.filter(payment_type='rental').aggregate(Sum('amount'))['amount__sum'] or 0.0
    revenue_late_fee = payment_scope.filter(payment_type='late_fee').aggregate(Sum('amount'))['amount__sum'] or 0.0
    refunded_deposits = payment_scope.filter(payment_type='refund').aggregate(Sum('amount'))['amount__sum'] or 0.0
    collected_deposits = SecurityDeposit.objects.filter(status='collected', **({} if is_admin(request.user) else {'order__created_by': request.user})).aggregate(Sum('amount'))['amount__sum'] or 0.0
    
    revenue_details = {
        'rental_revenue': revenue_rental,
        'late_fee_revenue': revenue_late_fee,
        'collected_deposits': collected_deposits,
        'refunded_deposits': refunded_deposits,
        'net_revenue': float(revenue_rental) + float(revenue_late_fee),
        'daily_revenue': payment_scope.filter(date__date=timezone.localdate(), payment_type__in=['rental', 'late_fee']).aggregate(Sum('amount'))['amount__sum'] or 0,
        'monthly_revenue': payment_scope.filter(date__year=timezone.localdate().year, date__month=timezone.localdate().month, payment_type__in=['rental', 'late_fee']).aggregate(Sum('amount'))['amount__sum'] or 0,
    }
    
    # 4. Deposit Report
    deposits = SecurityDeposit.objects.all().order_by('-collected_at') if is_admin(request.user) else SecurityDeposit.objects.filter(order__created_by=request.user).order_by('-collected_at')
    
    # 5. Late Fee Report
    late_fees = LateFee.objects.all().order_by('-created_at') if is_admin(request.user) else LateFee.objects.filter(order__created_by=request.user).order_by('-created_at')
    
    return render(request, 'reports/reports_home.html', {
        'rentals': rentals,
        'customers': customers,
        'revenue': revenue_details,
        'deposits': deposits,
        'late_fees': late_fees
    })
