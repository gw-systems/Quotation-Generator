"""
URL Configuration for quotations app
"""
from django.urls import path
from . import views

urlpatterns = [
    # List and detail views
    path('', views.quotation_list, name='quotation_list'),
    path('<int:pk>/', views.quotation_detail, name='quotation_detail'),
    
    # Create and update
    path('create/', views.quotation_create, name='quotation_create'),
    
    # Document downloads
    path('<int:pk>/download-docx/', views.download_docx, name='download_docx'),
    path('<int:pk>/download-pdf/', views.download_pdf, name='download_pdf'),
    
    # Email sending (deferred)
    path('<int:pk>/send-email/', views.send_email, name='send_email'),
    
    # AJAX endpoints
    # AJAX endpoints
    path('api/clients/create/', views.client_create_ajax, name='client_create_ajax'),
    
    # Client Management
    path('clients/', views.client_list, name='client_list'),
    path('clients/create/', views.client_create, name='client_create'),
    path('clients/<int:pk>/', views.client_detail, name='client_detail'),
    path('clients/<int:pk>/edit/', views.client_update, name='client_update'),
    path('clients/<int:pk>/toggle-status/', views.client_toggle_status, name='client_toggle_status'),
]
