from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class Client(models.Model):
    """Client/Customer information"""
    client_name = models.CharField(max_length=200, verbose_name="Client Name")
    company_name = models.CharField(max_length=200, verbose_name="Company Name")
    email = models.EmailField(verbose_name="Email Address")
    contact_number = models.CharField(max_length=10, verbose_name="Contact Number")
    address = models.TextField(verbose_name="Address")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active",
        help_text="Designates whether this client should be treated as active. Unselect this instead of deleting accounts."
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Client"
        verbose_name_plural = "Clients"
    
    def __str__(self):
        return f"{self.client_name} - {self.company_name}"


class ClientAudit(models.Model):
    """Audit trail for client actions"""
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('modified', 'Modified'),
        ('status_changed', 'Status Changed'),
    ]
    
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        verbose_name="Client"
    )
    
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        verbose_name="Action"
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="User"
    )
    
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp")
    
    # Store detailed change information
    changes = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Changes",
        help_text="Detailed information about what changed"
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP Address"
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Client Audit Log"
        verbose_name_plural = "Client Audit Logs"
    
    def __str__(self):
        return f"{self.client.client_name} - {self.get_action_display()} by {self.user} at {self.timestamp}"


class Quotation(models.Model):
    """Master quotation record"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    # Auto-generated quotation number
    quotation_number = models.CharField(
        max_length=50, 
        unique=True, 
        editable=False,
        verbose_name="Quotation Number"
    )
    
    # Client relationship
    client = models.ForeignKey(
        Client, 
        on_delete=models.PROTECT,
        related_name='quotations',
        verbose_name="Client"
    )
    
    # Quotation details
    date = models.DateField(auto_now_add=True, verbose_name="Quotation Date")
    validity_period = models.IntegerField(
        default=30,
        validators=[MinValueValidator(1)],
        verbose_name="Validity Period (Days)",
        help_text="Number of days this quotation is valid"
    )
    point_of_contact = models.CharField(
        max_length=200,
        verbose_name="Point of Contact",
        help_text="Sales person or contact person name"
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Status"
    )
    
    # Audit fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='quotations_created',
        verbose_name="Created By"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Quotation"
        verbose_name_plural = "Quotations"
    
    def __str__(self):
        return f"{self.quotation_number} - {self.client.company_name}"
    
    def save(self, *args, **kwargs):
        """Generate quotation number if not exists"""
        if not self.quotation_number:
            # Generate unique quotation number: GW-Q-YYYYMMDD-XXXX
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            # Get count of quotations created today for sequential number
            today_count = Quotation.objects.filter(
                quotation_number__startswith=f'GW-Q-{date_str}'
            ).count()
            self.quotation_number = f'GW-Q-{date_str}-{today_count + 1:04d}'
        super().save(*args, **kwargs)
    
    @property
    def subtotal(self):
        """Calculate subtotal of all locations"""
        return sum(location.subtotal for location in self.locations.all())
    
    @property
    def gst_amount(self):
        """Calculate GST of all locations"""
        return sum(location.gst_amount for location in self.locations.all())
    
    @property
    def grand_total(self):
        """Calculate grand total (Subtotal + GST)"""
        return self.subtotal + self.gst_amount
    
    @property
    def validity_date(self):
        """Calculate validity end date"""
        from datetime import timedelta
        return self.date + timedelta(days=self.validity_period)



class QuotationLocation(models.Model):
    """Location-specific pricing within a quotation"""
    
    quotation = models.ForeignKey(
        Quotation,
        on_delete=models.CASCADE,
        related_name='locations',
        verbose_name="Quotation"
    )
    
    location_name = models.CharField(
        max_length=100,
        verbose_name="Location Name",
        help_text="e.g., NCR, Bhiwandi, Mumbai"
    )
    
    order = models.IntegerField(
        default=0,
        verbose_name="Display Order"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Quotation Location"
        verbose_name_plural = "Quotation Locations"
    
    def __str__(self):
        return f"{self.quotation.quotation_number} - {self.location_name}"
    
    @property
    def subtotal(self):
        """Calculate subtotal for this location"""
        from decimal import Decimal
        total = Decimal('0.00')
        for item in self.items.all():
            if item.is_calculated:
                total += item.total
        return total
    
    @property
    def gst_amount(self):
        """Calculate GST for this location"""
        from django.conf import settings
        from decimal import Decimal
        gst_rate = Decimal(str(getattr(settings, 'GST_RATE', 0.18)))
        return self.subtotal * gst_rate
    
    @property
    def grand_total(self):
        """Calculate grand total for this location"""
        return self.subtotal + self.gst_amount


class QuotationItem(models.Model):
    """Line items in a quotation"""
    
    ITEM_CHOICES = [
        ('storage_charges', 'Storage Charges (per pallet per month)'),
        ('inbound_handling', 'Inbound Handling (per unit)'),
        ('outbound_handling', 'Outbound Handling (per unit)'),
        ('pick_pack', 'Pick & Pack (per order)'),
        ('packaging_material', 'Packaging Material'),
        ('labelling_services', 'Labelling Services'),
        ('wms_platform', 'WMS Platform Access (monthly per pallet)'),
        ('value_added', 'Value-Added Services'),
    ]
    
    
    # Location this item belongs to
    location = models.ForeignKey(
        QuotationLocation,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Location",
        null=True,  # Temporarily nullable for migration
        blank=True
    )
    
    # Keep quotation FK temporarily for migration
    quotation = models.ForeignKey(
        Quotation,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Quotation",
        null=True,  # Made nullable for migration
        blank=True
    )
    
    item_description = models.CharField(
        max_length=100,
        choices=ITEM_CHOICES,
        verbose_name="Item Description"
    )
    
    unit_cost = models.CharField(
        max_length=50,
        verbose_name="Unit Cost (₹)",
        help_text="Enter amount or 'as applicable'"
    )
    
    quantity = models.CharField(
        max_length=50,
        verbose_name="Quantity",
        help_text="Enter quantity or 'at actual'"
    )
    
    # Order for sorting items in quotation
    order = models.IntegerField(default=0, verbose_name="Order")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = "Quotation Item"
        verbose_name_plural = "Quotation Items"
    
    def __str__(self):
        return f"{self.get_item_description_display()} - {self.quotation.quotation_number}"
    
    @property
    def total(self):
        """Calculate total for this line item"""
        # Skip calculation if either field has 'at actual'
        unit_lower = str(self.unit_cost).lower()
        qty_lower = str(self.quantity).lower()
        
        if unit_lower == 'at actual' or qty_lower == 'at actual':
            return Decimal('0.00')
        
        try:
            cost = Decimal(str(self.unit_cost))
            qty = Decimal(str(self.quantity))
            return cost * qty
        except (ValueError, Exception):
            return Decimal('0.00')
    
    @property
    def is_calculated(self):
        """Check if this item should be included in calculations"""
        return str(self.unit_cost).lower() != 'at actual' and str(self.quantity).lower() != 'at actual'
    
    @property
    def display_unit_cost(self):
        """Get formatted unit cost for display"""
        unit_lower = str(self.unit_cost).lower()
        if unit_lower == 'at actual':
            return 'At Actual'
        try:
            return f"₹ {Decimal(str(self.unit_cost)):,.2f}"
        except (ValueError, Exception):
            return self.unit_cost
    
    @property
    def display_quantity(self):
        """Get formatted quantity for display"""
        qty_lower = str(self.quantity).lower()
        if qty_lower == 'at actual':
            return 'At Actual'
        return self.quantity
    
    @property
    def display_description(self):
        """Get description to display"""
        return self.get_item_description_display()


class QuotationAudit(models.Model):
    """Audit trail for quotation actions"""
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('modified', 'Modified'),
        ('docx_generated', 'DOCX Generated'),
        ('pdf_generated', 'PDF Generated'),
        ('email_sent', 'Email Sent'),
        ('status_changed', 'Status Changed'),
        ('downloaded', 'Downloaded'),
    ]
    
    quotation = models.ForeignKey(
        Quotation,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        verbose_name="Quotation"
    )
    
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        verbose_name="Action"
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="User"
    )
    
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp")
    
    # Store detailed change information
    changes = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Changes",
        help_text="Detailed information about what changed"
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP Address"
    )
    
    additional_metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Additional Metadata"
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Quotation Audit Log"
        verbose_name_plural = "Quotation Audit Logs"
    
    def __str__(self):
        return f"{self.quotation.quotation_number} - {self.get_action_display()} by {self.user} at {self.timestamp}"
