from django.urls import path
from . import views

app_name = 'rentals'

urlpatterns = [
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<str:item_key>/', views.cart_remove, name='cart_remove'),
    path('cart/clear/', views.cart_clear, name='cart_clear'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('products/search/', views.product_search_ajax, name='product_search_ajax'),
    path('orders/walk-in/create/', views.walk_in_order_create, name='walk_in_order_create'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/pickup/', views.pickup_confirm, name='pickup_confirm'),
    path('orders/<int:pk>/return/', views.return_confirm, name='return_confirm'),
]
