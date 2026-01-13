from django.test import TestCase
from decimal import Decimal
from quotations.models import Quotation, Client, QuotationLocation, QuotationItem

class QuotationTotalsTest(TestCase):
    def setUp(self):
        self.client = Client.objects.create(
            client_name="Test Client",
            company_name="Test Company",
            email="test@example.com",
            contact_number="1234567890",
            address="Test Address"
        )
        self.quotation = Quotation.objects.create(
            client=self.client,
            point_of_contact="TestUser"
        )
        self.location = QuotationLocation.objects.create(
            quotation=self.quotation,
            location_name="Test Location"
        )

    def test_quotation_totals_aggregation(self):
        """Test that quotation totals are aggregated from locations"""
        # Create items for the location
        # Item 1: 10 * 10 = 100
        QuotationItem.objects.create(
            location=self.location,
            quotation=self.quotation, # Legacy FK
            item_description='storage_charges',
            unit_cost="10.00",
            quantity="10",
        )
        # Item 2: 20 * 5 = 100
        QuotationItem.objects.create(
            location=self.location,
            quotation=self.quotation, # Legacy FK
            item_description='inbound_handling',
            unit_cost="20.00",
            quantity="5",
        )
        
        # Location Subtotal = 200
        # Location GST = 200 * 0.18 = 36
        # Location Total = 236
        
        self.assertEqual(self.quotation.subtotal, Decimal('200.00'))
        self.assertEqual(self.quotation.gst_amount, Decimal('36.00'))
        self.assertEqual(self.quotation.grand_total, Decimal('236.00'))

    def test_multiple_locations_totals(self):
        """Test totals with multiple locations"""
        # Location 1: 100
        QuotationItem.objects.create(
            location=self.location,
            quotation=self.quotation,
            item_description='storage_charges',
            unit_cost="10.00",
            quantity="10",
        )
        
        # Location 2
        location2 = QuotationLocation.objects.create(
            quotation=self.quotation,
            location_name="Test Location 2"
        )
        # Location 2 Item: 50 * 2 = 100
        QuotationItem.objects.create(
            location=location2,
            quotation=self.quotation,
            item_description='pick_pack',
            unit_cost="50.00",
            quantity="2",
        )
        
        # Total Subtotal = 100 + 100 = 200
        self.assertEqual(self.quotation.subtotal, Decimal('200.00'))
        self.assertEqual(self.quotation.gst_amount, Decimal('36.00'))
        self.assertEqual(self.quotation.grand_total, Decimal('236.00'))
