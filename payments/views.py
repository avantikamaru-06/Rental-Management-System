from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Payment, Invoice
from customers.models import Customer
from accounts.permissions import is_admin, is_salesperson

@login_required
def invoice_list(request):
    is_admin_user = is_admin(request.user)
    if is_admin_user:
        invoices = Invoice.objects.all().order_by('-id')
    elif is_salesperson(request.user):
        invoices = Invoice.objects.filter(order__created_by=request.user).order_by('-id')
    else:
        try:
            customer = request.user.customer_profile
            invoices = Invoice.objects.filter(order__customer=customer).order_by('-id')
        except Customer.DoesNotExist:
            invoices = Invoice.objects.none()
            
    return render(request, 'payments/invoice_list.html', {
        'invoices': invoices,
        'is_admin': is_admin_user
    })

@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    is_admin_user = is_admin(request.user)
    
    if not is_admin_user and not (is_salesperson(request.user) and invoice.order.created_by == request.user) and invoice.order.customer.user != request.user:
        messages.error(request, "Access denied.")
        return redirect('payments:invoice_list')
        
    order = invoice.order
    items = order.items.all()
    payments = order.payments.all()
    
    return render(request, 'payments/invoice_detail.html', {
        'invoice': invoice,
        'order': order,
        'items': items,
        'payments': payments,
        'is_admin': is_admin_user
    })

@login_required
def payment_list(request):
    is_admin_user = is_admin(request.user)
    if is_admin_user:
        payments = Payment.objects.all().order_by('-id')
    elif is_salesperson(request.user):
        payments = Payment.objects.filter(order__created_by=request.user).order_by('-id')
    else:
        try:
            customer = request.user.customer_profile
            payments = Payment.objects.filter(order__customer=customer).order_by('-id')
        except Customer.DoesNotExist:
            payments = Payment.objects.none()
            
    return render(request, 'payments/payment_list.html', {
        'payments': payments,
        'is_admin': is_admin_user
    })
