"""
Forms for quotation management
"""
from django import forms
from django.forms import inlineformset_factory
from decimal import Decimal, InvalidOperation
from .models import Client, Quotation, QuotationLocation, QuotationItem
from django.db import models


class ClientForm(forms.ModelForm):
    """Form for creating/editing clients"""
    
    class Meta:
        model = Client
        fields = ['client_name', 'company_name', 'email', 'contact_number', 'address']
        widgets = {
            'client_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter client name',
                'required': True
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter company name',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'client@example.com',
                'required': True
            }),
            'contact_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '10-digit phone number',
                'required': True,
                'type': 'tel',
                'pattern': '[0-9]{10}',
                'title': 'Please enter exactly 10 digits',
                'maxlength': '10',
                'minlength': '10'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter complete address',
                'required': True
            }),
        }
    
    def clean_client_name(self):
        """Validate client name"""
        client_name = self.cleaned_data.get('client_name')
        if not client_name or not client_name.strip():
            raise forms.ValidationError('Client name is required')
        return client_name.strip()
    
    def clean_company_name(self):
        """Validate company name"""
        company_name = self.cleaned_data.get('company_name')
        if not company_name or not company_name.strip():
            raise forms.ValidationError('Company name is required')
        return company_name.strip()
    
    def clean_email(self):
        """Validate email"""
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError('Email is required')
        # Django's EmailField already validates format
        return email.lower()
    
    def clean_contact_number(self):
        """Validate contact number"""
        import re
        contact = self.cleaned_data.get('contact_number')
        if not contact or not contact.strip():
            raise forms.ValidationError('Contact number is required')
        
        # Remove any spaces or formatting
        contact_clean = contact.strip().replace(' ', '').replace('-', '')
        
        # Must be exactly 10 digits
        if not re.match(r'^[0-9]{10}$', contact_clean):
            raise forms.ValidationError('Contact number must be exactly 10 digits')
        
        return contact_clean
    
    def clean_address(self):
        """Validate address"""
        address = self.cleaned_data.get('address')
        if not address or not address.strip():
            raise forms.ValidationError('Address is required')
        return address.strip()


class QuotationForm(forms.ModelForm):
    """Form for creating/editing quotations"""
    
    class Meta:
        model = Quotation
        fields = ['client', 'validity_period', 'point_of_contact', 'status']
        widgets = {
            'client': forms.Select(attrs={
                'class': 'form-control',
                'id': 'client-select',
                'required': True
            }),
            'validity_period': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '30',
                'min': '1',
                'required': True
            }),
            'point_of_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sales person name',
                'required': True
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter only active clients for new quotations
        if not self.instance.pk:
            self.fields['client'].queryset = Client.objects.filter(is_active=True)
            self.fields['validity_period'].initial = 30
        else:
            # For existing quotations, include the current client even if inactive
            current_client_id = self.instance.client_id
            self.fields['client'].queryset = Client.objects.filter(
                models.Q(is_active=True) | models.Q(id=current_client_id)
            )
    
    def clean_validity_period(self):
        """Validate validity period"""
        period = self.cleaned_data.get('validity_period')
        if not period or period < 1:
            raise forms.ValidationError('Validity period must be at least 1 day')
        if period > 365:
            raise forms.ValidationError('Validity period cannot exceed 365 days')
        return period
    
    def clean_point_of_contact(self):
        """Validate point of contact"""
        poc = self.cleaned_data.get('point_of_contact')
        if not poc or not poc.strip():
            raise forms.ValidationError('Point of contact is required')
        return poc.strip()


class QuotationItemForm(forms.ModelForm):
    """Form for quotation line items"""
    
    class Meta:
        model = QuotationItem
        fields = ['item_description', 'storage_unit_type', 'unit_cost', 'quantity', 'order']
        widgets = {
            'item_description': forms.Select(attrs={
                'class': 'form-control item-description',
                'required': True
            }),
            'storage_unit_type': forms.Select(attrs={
                'class': 'form-select form-select-sm mt-1 storage-unit-type',
                'style': 'display: none;'
            }),
            'unit_cost': forms.TextInput(attrs={
                'class': 'form-control unit-cost',
                'placeholder': 'At actual',
                'required': False
            }),
            'quantity': forms.TextInput(attrs={
                'class': 'form-control quantity',
                'placeholder': 'At actual',
                'required': False
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'type': 'hidden'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make unit_cost and quantity not required since empty = 'at actual'
        self.fields['unit_cost'].required = False
        self.fields['quantity'].required = False
    
    def clean_unit_cost(self):
        """Validate unit cost - accepts numbers, empty, or 'at actual'"""
        cost = self.cleaned_data.get('unit_cost', '').strip()
        
        # Default to 'at actual' if empty or 0
        if not cost or cost == '0' or cost == '0.00':
            return 'at actual'
        
        # Accept 'at actual' from user (normalize to lowercase)
        if cost.lower() == 'at actual':
            return 'at actual'
        
        # Must be a valid positive number
        try:
            cost_decimal = Decimal(str(cost))
            if cost_decimal < 0:
                raise forms.ValidationError('Unit cost must be positive')
            return str(cost_decimal)
        except (ValueError, InvalidOperation):
            raise forms.ValidationError('Please enter a valid number or "at actual"')
    
    def clean_quantity(self):
        """Validate quantity - accepts numbers, empty, or 'at actual'"""
        qty = self.cleaned_data.get('quantity', '').strip()
        
        # Default to 'at actual' if empty or 0
        if not qty or qty == '0' or qty == '0.00':
            return 'at actual'
        
        # Accept 'at actual' from user (normalize to lowercase)
        if qty.lower() == 'at actual':
            return 'at actual'
        
        # Must be a valid positive number
        try:
            qty_decimal = Decimal(str(qty))
            if qty_decimal <= 0:
                return 'at actual'  # Convert 0 or negative to 'at actual'
            return str(qty_decimal)
        except (ValueError, InvalidOperation):
            raise forms.ValidationError('Please enter a valid number or "at actual"')



class QuotationLocationForm(forms.ModelForm):
    """Form for creating/editing quotation locations"""
    
    class Meta:
        model = QuotationLocation
        fields = ['location_name', 'order']
        widgets = {
            'location_name': forms.TextInput(attrs={
                'class': 'form-control location-name',
                'placeholder': 'e.g., NCR, Bhiwandi, Mumbai',
                'required': True
            }),
            'order': forms.HiddenInput(),
        }
    
    def clean_location_name(self):
        """Validate location name"""
        name = self.cleaned_data.get('location_name', '').strip()
        if not name:
            raise forms.ValidationError('Location name is required')
        return name


# Create formset for quotation locations
QuotationLocationFormSet = inlineformset_factory(
    Quotation,
    QuotationLocation,
    form=QuotationLocationForm,
    extra=0,  # Don't show extra empty forms - min_num will ensure at least 1
    can_delete=True,
    min_num=1,  # At least one location required
    validate_min=True,
)


# Create formset for quotation items (now per location)
QuotationItemFormSet = inlineformset_factory(
    QuotationLocation,  # Changed from Quotation to QuotationLocation
    QuotationItem,
    form=QuotationItemForm,
    extra=3,  # Show 3 empty forms by default
    can_delete=True,
    min_num=0,  # No minimum required
    validate_min=False,
)


class EmailQuotationForm(forms.Form):
    """Form for sending quotation via email (deferred)"""
    
    recipient_email = forms.EmailField(
        label="Recipient Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'client@example.com'
        })
    )
    
    cc_emails = forms.CharField(
        label="CC (optional)",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'email1@example.com, email2@example.com'
        }),
        help_text="Separate multiple emails with commas"
    )
    
    include_docx = forms.BooleanField(
        label="Attach DOCX",
        required=False,
        initial=True
    )
    
    include_pdf = forms.BooleanField(
        label="Attach PDF",
        required=False,
        initial=True
    )
    
    def clean_cc_emails(self):
        """Parse and validate CC emails"""
        cc_emails = self.cleaned_data.get('cc_emails', '')
        if not cc_emails:
            return []
        
        # Split by comma and clean
        emails = [email.strip() for email in cc_emails.split(',')]
        
        # Validate each email
        validated_emails = []
        for email in emails:
            if email:
                try:
                    forms.EmailField().clean(email)
                    validated_emails.append(email)
                except forms.ValidationError:
                    raise forms.ValidationError(f"Invalid email address: {email}")
        
        return validated_emails
