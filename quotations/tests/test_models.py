"""
Tests for models including Client, Quotation, QuotationLocation, and QuotationItem
"""
import pytest
from decimal import Decimal
from quotations.models import Client, Quotation, QuotationLocation, QuotationItem


@pytest.mark.django_db
class TestClientModel:
    """Test Client model"""
    
    def test_create_client(self):
        """Test creating a client"""
        client = Client.objects.create(
            client_name="John Doe",
            company_name="Test Company",
            email="john@test.com",
            contact_number="9876543210",
            address="123 Test Street"
        )
        assert client.client_name == "John Doe"
        assert client.company_name == "Test Company"
        assert str(client) == "John Doe - Test Company"
    
    def test_client_str_representation(self):
        """Test client string representation"""
        client = Client.objects.create(
            client_name="Jane Smith",
            company_name="ABC Corp",
            email="jane@abc.com",
            contact_number="9123456780",
            address="456 Main St"
        )
        assert "Jane Smith" in str(client)
        assert "ABC Corp" in str(client)


@pytest.mark.django_db
class TestQuotationModel:
    """Test Quotation model"""
    
    def test_create_quotation(self):
        """Test creating a quotation"""
        client = Client.objects.create(
            client_name="Test Client",
            company_name="Test Co",
            email="test@test.com",
            contact_number="9999999999",
            address="Test Address"
        )
        
        quotation = Quotation.objects.create(
            client=client,
            validity_period=30,
            point_of_contact="Sales Person"
        )
        
        assert quotation.client == client
        assert quotation.validity_period == 30
        assert quotation.quotation_number.startswith("GW-Q-")
    
    def test_quotation_number_generation(self):
        """Test auto-generation of quotation number"""
        client = Client.objects.create(
            client_name="Test",
            company_name="Test",
            email="test@test.com",
            contact_number="9999999999",
            address="Test"
        )
        
        q1 = Quotation.objects.create(client=client, point_of_contact="Test")
        q2 = Quotation.objects.create(client=client, point_of_contact="Test")
        
        assert q1.quotation_number != q2.quotation_number
        assert "GW-Q-" in q1.quotation_number


@pytest.mark.django_db
class TestQuotationLocation:
    """Test QuotationLocation model"""
    
    def test_create_location(self):
        """Test creating a location"""
        client = Client.objects.create(
            client_name="Test",
            company_name="Test",
            email="test@test.com",
            contact_number="9999999999",
            address="Test"
        )
        quotation = Quotation.objects.create(client=client, point_of_contact="Test")
        
        location = QuotationLocation.objects.create(
            quotation=quotation,
            location_name="NCR",
            order=0
        )
        
        assert location.location_name == "NCR"
        assert location.quotation == quotation
        assert "NCR" in str(location)
    
    def test_location_subtotal_calculation(self):
        """Test location subtotal calculation"""
        client = Client.objects.create(
            client_name="Test",
            company_name="Test",
            email="test@test.com",
            contact_number="9999999999",
            address="Test"
        )
        quotation = Quotation.objects.create(client=client, point_of_contact="Test")
        location = QuotationLocation.objects.create(
            quotation=quotation,
            location_name="NCR",
            order=0
        )
        
        # Add items to location
        QuotationItem.objects.create(
            location=location,
            item_description="storage_charges",
            unit_cost="100.00",
            quantity="5"
        )
        QuotationItem.objects.create(
            location=location,
            item_description="inbound_handling",
            unit_cost="50.00",
            quantity="10"
        )
        
        # 100*5 + 50*10 = 500 + 500 = 1000
        assert location.subtotal == Decimal("1000.00")
    
    def test_location_gst_calculation(self):
        """Test location GST calculation"""
        client = Client.objects.create(
            client_name="Test",
            company_name="Test",
            email="test@test.com",
            contact_number="9999999999",
            address="Test"
        )
        quotation = Quotation.objects.create(client=client, point_of_contact="Test")
        location = QuotationLocation.objects.create(
            quotation=quotation,
            location_name="Bhiwandi",
            order=0
        )
        
        QuotationItem.objects.create(
            location=location,
            item_description="storage_charges",
            unit_cost="1000.00",
            quantity="1"
        )
        
        # Subtotal = 1000, GST @ 18% = 180
        assert location.subtotal == Decimal("1000.00")
        assert location.gst_amount == Decimal("180.00")
        assert location.grand_total == Decimal("1180.00")
    
    def test_location_with_at_actual_items(self):
        """Test location totals exclude 'at actual' items"""
        client = Client.objects.create(
            client_name="Test",
            company_name="Test",
            email="test@test.com",
            contact_number="9999999999",
            address="Test"
        )
        quotation = Quotation.objects.create(client=client, point_of_contact="Test")
        location = QuotationLocation.objects.create(
            quotation=quotation,
            location_name="Mumbai",
            order=0
        )
        
        # One numeric item
        QuotationItem.objects.create(
            location=location,
            item_description="storage_charges",
            unit_cost="500.00",
            quantity="2"
        )
        # One 'at actual' item
        QuotationItem.objects.create(
            location=location,
            item_description="value_added",
            unit_cost="at actual",
            quantity="at actual"
        )
        
        # Only numeric item should be included: 500 * 2 = 1000
        assert location.subtotal == Decimal("1000.00")
    
    def test_multiple_locations_per_quotation(self):
        """Test quotation can have multiple locations"""
        client = Client.objects.create(
            client_name="Test",
            company_name="Test",
            email="test@test.com",
            contact_number="9999999999",
            address="Test"
        )
        quotation = Quotation.objects.create(client=client, point_of_contact="Test")
        
        location1 = QuotationLocation.objects.create(
            quotation=quotation,
            location_name="NCR",
            order=0
        )
        location2 = QuotationLocation.objects.create(
            quotation=quotation,
            location_name="Bhiwandi",
            order=1
        )
        
        assert quotation.locations.count() == 2
        assert location1 in quotation.locations.all()
        assert location2 in quotation.locations.all()


@pytest.mark.django_db
class TestQuotationItem:
    """Test QuotationItem model"""
    
    def test_item_total_calculation(self):
        """Test total calculation for numeric values"""
        client = Client.objects.create(
            client_name="Test",
            company_name="Test",
            email="test@test.com",
            contact_number="9999999999",
            address="Test"
        )
        quotation = Quotation.objects.create(client=client, point_of_contact="Test")
        location = QuotationLocation.objects.create(
            quotation=quotation,
            location_name="NCR",
            order=0
        )
        
        item = QuotationItem.objects.create(
            location=location,
            item_description="storage_charges",
            unit_cost="100.00",
            quantity="5"
        )
        
        assert item.total == Decimal("500.00")
    
    def test_item_with_at_actual(self):
        """Test item with 'at actual' values"""
        client = Client.objects.create(
            client_name="Test",
            company_name="Test",
            email="test@test.com",
            contact_number="9999999999",
            address="Test"
        )
        quotation = Quotation.objects.create(client=client, point_of_contact="Test")
        location = QuotationLocation.objects.create(
            quotation=quotation,
            location_name="NCR",
            order=0
        )
        
        item = QuotationItem.objects.create(
            location=location,
            item_description="storage_charges",
            unit_cost="at actual",
            quantity="at actual"
        )
        
        assert item.total == Decimal("0.00")
        assert not item.is_calculated
