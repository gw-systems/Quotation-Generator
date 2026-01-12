"""
Tests for forms
"""
import pytest
from decimal import Decimal
from quotations.forms import ClientForm, QuotationForm, QuotationItemForm
from quotations.models import Client


@pytest.mark.django_db
class TestClientForm:
    """Test ClientForm"""
    
    def test_valid_client_form(self):
        """Test form with valid data"""
        data = {
            'client_name': 'John Doe',
            'company_name': 'Test Company',
            'email': 'john@test.com',
            'contact_number': '9876543210',
            'address': '123 Test Street'
        }
        form = ClientForm(data=data)
        assert form.is_valid()
    
    def test_invalid_email(self):
        """Test form with invalid email"""
        data = {
            'client_name': 'John Doe',
            'company_name': 'Test Company',
            'email': 'invalid-email',
            'contact_number': '9876543210',
            'address': '123 Test Street'
        }
        form = ClientForm(data=data)
        assert not form.is_valid()
        assert 'email' in form.errors
    
    def test_invalid_phone_number(self):
        """Test form with invalid phone number"""
        data = {
            'client_name': 'John Doe',
            'company_name': 'Test Company',
            'email': 'john@test.com',
            'contact_number': '123',  # Too short
            'address': '123 Test Street'
        }
        form = ClientForm(data=data)
        assert not form.is_valid()
        assert 'contact_number' in form.errors


@pytest.mark.django_db
class TestQuotationItemForm:
    """Test QuotationItemForm"""
    
    def test_numeric_values(self):
        """Test form with numeric values"""
        data = {
            'item_description': 'storage_charges',
            'unit_cost': '100.00',
            'quantity': '5',
            'order': 0
        }
        form = QuotationItemForm(data=data)
        assert form.is_valid()
    
    def test_typing_at_actual_accepted(self):
        """Test that typing 'at actual' is now accepted and normalized"""
        data = {
            'item_description': 'storage_charges',
            'unit_cost': 'at actual',
            'quantity': 'at actual',
            'order': 0
        }
        form = QuotationItemForm(data=data)
        assert form.is_valid(), f"Form errors: {form.errors}"
        assert form.cleaned_data['unit_cost'] == 'at actual'
        assert form.cleaned_data['quantity'] == 'at actual'
    
    def test_empty_defaults_to_at_actual(self):
        """Test empty fields default to 'at actual'"""
        data = {
            'item_description': 'storage_charges',
            'unit_cost': '',
            'quantity': '',
            'order': 0
        }
        form = QuotationItemForm(data=data)
        assert form.is_valid(), f"Form errors: {form.errors}"
        assert form.cleaned_data['unit_cost'] == 'at actual'
        assert form.cleaned_data['quantity'] == 'at actual'
    
    def test_zero_converts_to_at_actual(self):
        """Test zero values convert to 'at actual'"""
        data = {
            'item_description': 'storage_charges',
            'unit_cost': '0',
            'quantity': '0',
            'order': 0
        }
        form = QuotationItemForm(data=data)
        assert form.is_valid()
        assert form.cleaned_data['unit_cost'] == 'at actual'
        assert form.cleaned_data['quantity'] == 'at actual'
    
    def test_negative_quantity_converts_to_at_actual(self):
        """Test negative quantity converts to 'at actual'"""
        data = {
            'item_description': 'storage_charges',
            'unit_cost': '100',
            'quantity': '-5',
            'order': 0
        }
        form = QuotationItemForm(data=data)
        assert form.is_valid()
        assert form.cleaned_data['quantity'] == 'at actual'
