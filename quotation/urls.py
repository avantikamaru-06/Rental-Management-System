from django.urls import path
from . import views

app_name = 'quotation'

urlpatterns = [
    path('', views.quotation_list, name='quotation_list'),
    path('<int:pk>/', views.quotation_detail, name='quotation_detail'),
    path('create/', views.quotation_create, name='quotation_create'),
    path('item/<int:pk>/delete/', views.quotation_item_delete, name='quotation_item_delete'),
    path('<int:pk>/send/', views.quotation_send, name='quotation_send'),
    path('<int:pk>/approve/', views.quotation_approve, name='quotation_approve'),
    path('<int:pk>/convert/', views.quotation_convert, name='quotation_convert'),
]
