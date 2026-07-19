from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Product, Category, RentalPeriod, Pricelist
from .forms import ProductForm
from accounts.permissions import is_admin

def product_list(request):
    products = Product.objects.all().order_by('-id')
    categories = Category.objects.all()
    
    # Search and Filter
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    brand = request.GET.get('brand')
    availability = request.GET.get('availability')
    
    if query:
        products = products.filter(name__icontains=query) | products.filter(description__icontains=query)
    if category_id:
        products = products.filter(category_id=category_id)
    if brand:
        products = products.filter(brand__iexact=brand)
    if availability:
        if availability == 'available':
            products = products.filter(is_available=True)
        elif availability == 'rented':
            products = products.filter(is_available=False)
            
    brands = Product.objects.values_list('brand', flat=True).distinct().exclude(brand__isnull=True).exclude(brand__exact='')
            
    return render(request, 'products/product_list.html', {
        'products': products,
        'categories': categories,
        'brands': brands,
        'selected_category': int(category_id) if category_id else None,
        'selected_brand': brand,
        'selected_availability': availability,
        'query': query,
        'is_admin': is_admin(request.user)
    })

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    periods = RentalPeriod.objects.all()
    pricelists = Pricelist.objects.filter(is_active=True)
    
    return render(request, 'products/product_detail.html', {
        'product': product,
        'periods': periods,
        'pricelists': pricelists,
        'is_admin': is_admin(request.user)
    })

@login_required
@user_passes_test(is_admin)
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Product '{product.name}' created successfully.")
            return redirect('products:product_list')
    else:
        form = ProductForm()
    return render(request, 'products/product_form.html', {'form': form, 'title': 'Add New Product'})

@login_required
@user_passes_test(is_admin)
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"Product '{product.name}' updated successfully.")
            return redirect('products:product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)
    return render(request, 'products/product_form.html', {'form': form, 'title': f"Edit Product: {product.name}"})

@login_required
@user_passes_test(is_admin)
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f"Product '{name}' deleted successfully.")
        return redirect('products:product_list')
    return render(request, 'products/product_confirm_delete.html', {'product': product})
