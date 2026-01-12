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
    path('<int:pk>/edit/', views.quotation_update, name='quotation_update'),
    
    # Document downloads
    path('<int:pk>/download-docx/', views.download_docx, name='download_docx'),
    path('<int:pk>/download-pdf/', views.download_pdf, name='download_pdf'),
    
    # Email sending (deferred)
    path('<int:pk>/send-email/', views.send_email, name='send_email'),
    
    # AJAX endpoints
    path('clients/create/', views.client_create_ajax, name='client_create_ajax'),
]
