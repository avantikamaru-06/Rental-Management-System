from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.urls import reverse
from .forms import UserRegistrationForm, UserUpdateForm, CustomerUpdateForm
from customers.models import Customer
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from .permissions import get_dashboard_url_name, is_customer

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    next_url = request.POST.get('next') or request.GET.get('next') or ''
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Registration details are deliberately kept in the session until
            # checkout succeeds. This avoids orphan customer records when a
            # prospective renter abandons or fails payment.
            request.session['pending_registration'] = {
                key: form.cleaned_data.get(key, '')
                for key in ('username', 'first_name', 'last_name', 'email', 'phone', 'saved_address')
            }
            request.session['pending_registration']['password_hash'] = make_password(form.cleaned_data['password'])
            if request.session.pop('checkout_after_auth', False):
                messages.success(request, "Your account is ready. Continue checkout to complete your rental.")
                return redirect(next_url or 'rentals:checkout')
            messages.success(request, "Your details are ready. Choose a product and complete payment to activate your account.")
            return redirect('products:product_list')
    else:
        form = UserRegistrationForm()
        
    return render(request, 'accounts/register.html', {'form': form, 'next_url': next_url})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    next_url = request.POST.get('next') or request.GET.get('next') or ''
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if next_url and ('checkout' in next_url or 'cart' in next_url):
            request.session['checkout_after_auth'] = True
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                # Only customer accounts have customer profiles.
                if is_customer(user) and not hasattr(user, 'customer_profile'):
                    Customer.objects.create(user=user)
                messages.success(request, f"Welcome back, {username}!")
                if request.session.pop('checkout_after_auth', False):
                    return redirect(next_url or 'rentals:checkout')
                return redirect(get_dashboard_url_name(user))
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    
    # Apply Bootstrap styling to Django's built-in auth form widgets
    form.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Username'})
    form.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        
    return render(request, 'accounts/login.html', {'form': form, 'next_url': next_url})

def logout_view(request):
    auth_logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('accounts:login')

@login_required
def profile_view(request):
    if not is_customer(request.user):
        return render(request, 'accounts/profile.html', {'u_form': UserUpdateForm(instance=request.user), 'c_form': None})
    # Ensure customer profile exists
    try:
        customer = request.user.customer_profile
    except Customer.DoesNotExist:
        customer = Customer.objects.create(user=request.user)

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        c_form = CustomerUpdateForm(request.POST, request.FILES, instance=customer)
        if u_form.is_valid() and c_form.is_valid():
            u_form.save()
            c_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('accounts:profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        c_form = CustomerUpdateForm(instance=customer)
        
    return render(request, 'accounts/profile.html', {
        'u_form': u_form,
        'c_form': c_form
    })

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if User.objects.filter(email=email).exists():
            messages.success(request, f"Password reset instructions have been simulated & sent to {email}.")
        else:
            messages.error(request, "No account matches that email address.")
        return redirect('accounts:login')
    return render(request, 'accounts/forgot_password.html')
