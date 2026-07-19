from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('salesperson/', views.salesperson_dashboard, name='salesperson_dashboard'),
    path('portal/', views.customer_dashboard, name='customer_dashboard'),
]
