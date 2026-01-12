"""
Views for quotation management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, HttpResponse, JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.core.paginator import Paginator
import os

from .models import Client, Quotation, QuotationLocation, QuotationItem
from .forms import ClientForm, QuotationForm, QuotationLocationFormSet, QuotationItemFormSet, EmailQuotationForm
from .services.document_generator import generate_quotation_docx
from .services.pdf_generator import generate_quotation_pdf_from_quotation
from .services.audit_service import log_quotation_action, get_client_ip
from .services.email_service import send_quotation_email


@login_required
def quotation_list(request):
    """List all quotations with search and filters"""
    quotations = Quotation.objects.all().select_related('client', 'created_by')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        quotations = quotations.filter(
            quotation_number__icontains=search_query
        ) | quotations.filter(
            client__client_name__icontains=search_query
        ) | quotations.filter(
            client__company_name__icontains=search_query
        )
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        quotations = quotations.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(quotations, 20)  # 20 quotations per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': Quotation.STATUS_CHOICES,
    }
    
    return render(request, 'quotations/quotation_list.html', context)


@login_required
def quotation_detail(request, pk):
    """View quotation details"""
    quotation = get_object_or_404(
        Quotation.objects.select_related('client', 'created_by').prefetch_related('locations__items', 'audit_logs'),
        pk=pk
    )
    
    context = {
        'quotation': quotation,
        'locations': quotation.locations.all().order_by('order'),
        'audit_logs': quotation.audit_logs.all()[:10],  # Show last 10 audit logs
    }
    
    return render(request, 'quotations/quotation_detail.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def quotation_create(request):
    """Create new quotation with nested location-item formsets"""
    if request.method == 'POST':
        quotation_form = QuotationForm(request.POST)
        location_formset = QuotationLocationFormSet(request.POST)
        
        # Collect all item formsets for each location
        item_formsets = []
        location_count = int(request.POST.get('locations-TOTAL_FORMS', 0))
        
        for i in range(location_count):
            # Create item formset with prefix for this location
            prefix = f'locations-{i}-items'
            item_formset = QuotationItemFormSet(request.POST, prefix=prefix)
            item_formsets.append((i, item_formset))
        
        # Validate all formsets
        all_valid = quotation_form.is_valid() and location_formset.is_valid()
        for _, item_formset in item_formsets:
            if not item_formset.is_valid():
                all_valid = False
        
        if all_valid:
            with transaction.atomic():
                # Save quotation
                quotation = quotation_form.save(commit=False)
                quotation.created_by = request.user
                quotation.save()
                
                # Save locations
                location_formset.instance = quotation
                locations = location_formset.save()
                
                # Save items for each location
                for i, item_formset in item_formsets:
                    # Get the corresponding location (filter out deleted ones)
                    location_forms = [f for f in location_formset.forms if not f.cleaned_data.get('DELETE', False)]
                    if i < len(location_forms):
                        location_instance = location_forms[i].instance
                        item_formset.instance = location_instance
                        items_saved = item_formset.save(commit=True)
                        print(f"[SAVE] Location {i} ({location_instance.location_name}): Saved {len(items_saved)} items")
                        for item in items_saved:
                            print(f"  - {item.display_description}: cost={item.unit_cost}, qty={item.quantity}")
                
                # Log audit trail
                log_quotation_action(
                    quotation=quotation,
                    action='created',
                    user=request.user,
                    ip_address=get_client_ip(request)
                )
                
                messages.success(request, f'Quotation {quotation.quotation_number} created successfully!')
                return redirect('quotation_detail', pk=quotation.pk)
        else:
            # Debug: print all errors
            print("\n=== VALIDATION ERRORS ===")
            if not quotation_form.is_valid():
                print("Quotation form errors:", quotation_form.errors)
            if not location_formset.is_valid():
                print("Location formset errors:", location_formset.errors)
                print("Location formset non_form_errors:", location_formset.non_form_errors())
                for i, form in enumerate(location_formset.forms):
                    if form.errors:
                        print(f"  Location {i} errors:", form.errors)
            for i, item_formset in item_formsets:
                if not item_formset.is_valid():
                    print(f"Item formset {i} errors:", item_formset.errors)
                    print(f"Item formset {i} non_form_errors:", item_formset.non_form_errors())
                    for j, form in enumerate(item_formset.forms):
                        if form.errors:
                            print(f"  Location {i}, Item {j} errors:", form.errors)
            print("=========================\n")
            messages.error(request, 'Please correct the errors below. Check console for details.')
    else:
        quotation_form = QuotationForm()
        location_formset = QuotationLocationFormSet()
    
    context = {
        'quotation_form': quotation_form,
        'location_formset': location_formset,
        'clients': Client.objects.all(),
        'is_edit': False,
    }
    
    return render(request, 'quotations/quotation_form.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def quotation_update(request, pk):
    """Update existing quotation with nested location-item formsets"""
    quotation = get_object_or_404(Quotation, pk=pk)
    
    # Only allow editing draft quotations
    if quotation.status != 'draft':
        messages.warning(request, 'Only draft quotations can be edited.')
        return redirect('quotation_detail', pk=quotation.pk)
    
    if request.method == 'POST':
        quotation_form = QuotationForm(request.POST, instance=quotation)
        location_formset = QuotationLocationFormSet(request.POST, instance=quotation)
        
        # Collect all item formsets for each location
        item_formsets = []
        location_count = int(request.POST.get('locations-TOTAL_FORMS', 0))
        
        # Get existing locations to match with formsets
        existing_locations = list(quotation.locations.all().order_by('order'))
        
        for i in range(location_count):
            prefix = f'locations-{i}-items'
            # Try to get existing location if available
            location_instance = existing_locations[i] if i < len(existing_locations) else None
            item_formset = QuotationItemFormSet(request.POST, prefix=prefix, instance=location_instance)
            item_formsets.append((i, item_formset))
        
        # Validate all formsets
        all_valid = quotation_form.is_valid() and location_formset.is_valid()
        for _, item_formset in item_formsets:
            if not item_formset.is_valid():
                all_valid = False
        
        if all_valid:
            with transaction.atomic():
                quotation = quotation_form.save()
                
                # Save locations
                locations = location_formset.save()
                
                # Save items for each location
                for i, item_formset in item_formsets:
                    # Get the corresponding location
                    location_forms = [f for f in location_formset.forms if not f.cleaned_data.get('DELETE', False)]
                    if i < len(location_forms):
                        location_instance = location_forms[i].instance
                        item_formset.instance = location_instance
                        item_formset.save()
                
                # Log audit trail
                log_quotation_action(
                    quotation=quotation,
                    action='modified',
                    user=request.user,
                    ip_address=get_client_ip(request),
                    changes={'message': 'Quotation updated'}
                )
                
                messages.success(request, 'Quotation updated successfully!')
                return redirect('quotation_detail', pk=quotation.pk)
        else:
            if not quotation_form.is_valid():
                print("Quotation form errors:", quotation_form.errors)
            if not location_formset.is_valid():
                print("Location formset errors:", location_formset.errors)
            for i, item_formset in item_formsets:
                if not item_formset.is_valid():
                    print(f"Item formset {i} errors:", item_formset.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        quotation_form = QuotationForm(instance=quotation)
        location_formset = QuotationLocationFormSet(instance=quotation)
    
    context = {
        'quotation_form': quotation_form,
        'location_formset': location_formset,
        'quotation': quotation,
        'clients': Client.objects.all(),
        'is_edit': True,
    }
    
    return render(request, 'quotations/quotation_form.html', context)


@login_required
@require_http_methods(["POST"])
def client_create_ajax(request):
    """Create client via AJAX from quotation form"""
    form = ClientForm(request.POST)
    
    if form.is_valid():
        client = form.save()
        return JsonResponse({
            'success': True,
            'client': {
                'id': client.id,
                'name': str(client)
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


@login_required
def download_docx(request, pk):
    """Download quotation as DOCX"""
    quotation = get_object_or_404(Quotation, pk=pk)
    
    try:
        # Generate DOCX
        docx_path = generate_quotation_docx(quotation)
        
        # Log audit trail
        log_quotation_action(
            quotation=quotation,
            action='docx_generated',
            user=request.user,
            ip_address=get_client_ip(request)
        )
        
        # Serve file
        response = FileResponse(
            open(docx_path, 'rb'),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = f'attachment; filename="{quotation.quotation_number}.docx"'
        
        return response
    
    except Exception as e:
        messages.error(request, f'Failed to generate DOCX: {str(e)}')
        return redirect('quotation_detail', pk=quotation.pk)


@login_required
def download_pdf(request, pk):
    """Download quotation as PDF"""
    quotation = get_object_or_404(Quotation, pk=pk)
    
    try:
        # Generate PDF
        pdf_path = generate_quotation_pdf_from_quotation(quotation)
        
        # Log audit trail
        log_quotation_action(
            quotation=quotation,
            action='pdf_generated',
            user=request.user,
            ip_address=get_client_ip(request)
        )
        
        # Serve file
        response = FileResponse(
            open(pdf_path, 'rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="{quotation.quotation_number}.pdf"'
        
        return response
    
    except Exception as e:
        messages.error(request, f'Failed to generate PDF: {str(e)}')
        return redirect('quotation_detail', pk=quotation.pk)


@login_required
@require_http_methods(["GET", "POST"])
def send_email(request, pk):
    """Send quotation via email (deferred)"""
    quotation = get_object_or_404(Quotation, pk=pk)
    
    if request.method == 'POST':
        form = EmailQuotationForm(request.POST)
        
        if form.is_valid():
            try:
                # Generate documents if requested
                docx_path = None
                pdf_path = None
                
                if form.cleaned_data['include_docx']:
                    docx_path = generate_quotation_docx(quotation)
                
                if form.cleaned_data['include_pdf']:
                    pdf_path = generate_quotation_pdf_from_quotation(quotation)
                
                # Send email
                success = send_quotation_email(
                    quotation=quotation,
                    recipient_email=form.cleaned_data['recipient_email'],
                    docx_path=docx_path,
                    pdf_path=pdf_path,
                    cc_emails=form.cleaned_data['cc_emails']
                )
                
                if success:
                    # Log audit trail
                    log_quotation_action(
                        quotation=quotation,
                        action='email_sent',
                        user=request.user,
                        ip_address=get_client_ip(request),
                        metadata={'recipient': form.cleaned_data['recipient_email']}
                    )
                    
                    # Update status to sent if it was draft
                    if quotation.status == 'draft':
                        quotation.status = 'sent'
                        quotation.save()
                    
                    messages.success(request, 'Quotation sent successfully!')
                    return redirect('quotation_detail', pk=quotation.pk)
                else:
                    messages.error(request, 'Failed to send email. Please check email configuration.')
            
            except Exception as e:
                messages.error(request, f'Failed to send email: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Pre-fill with client email
        form = EmailQuotationForm(initial={
            'recipient_email': quotation.client.email
        })
    
    context = {
        'quotation': quotation,
        'form': form,
    }
    
    return render(request, 'quotations/send_email.html', context)
