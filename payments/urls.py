from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('history/', views.payment_list, name='payment_list'),
]
