
import pytest
from unittest.mock import MagicMock, patch
from quotations.models import Client, Quotation, ClientAudit, QuotationAudit
from quotations.services.audit_service import (
    log_client_action, 
    log_quotation_action, 
    get_client_ip,
    track_client_changes,
    track_quotation_changes
)
from quotations.services.email_service import send_quotation_email

@pytest.fixture
def sample_data(db):
    client = Client.objects.create(
        client_name="Test Client",
        company_name="Test Company",
        email="test@example.com",
        contact_number="123",
        address="Addr"
    )
    quotation = Quotation.objects.create(
        client=client, 
        point_of_contact="Test POC",
        validity_period=30
    )
    return client, quotation

@pytest.mark.django_db
class TestAuditService:
    def test_log_client_action(self, sample_data):
        """Test logging client action"""
        client, _ = sample_data
        
        log_client_action(client, 'created', None, changes={'field': 'value'})
        
        audit = ClientAudit.objects.first()
        assert audit.client == client
        assert audit.action == 'created'
        assert audit.changes == {'field': 'value'}

    def test_log_quotation_action(self, sample_data):
        """Test logging quotation action"""
        _, quotation = sample_data
        
        log_quotation_action(quotation, 'modified', None, changes={'status': 'draft'})
        
        audit = QuotationAudit.objects.first()
        assert audit.quotation == quotation
        assert audit.action == 'modified'
        assert audit.changes == {'status': 'draft'}

    def test_get_client_ip(self):
        """Test IP extraction"""
        req_proxy = MagicMock()
        req_proxy.META = {'HTTP_X_FORWARDED_FOR': '10.0.0.1, 192.168.1.1'}
        assert get_client_ip(req_proxy) == '10.0.0.1'
        
        req_direct = MagicMock()
        req_direct.META = {'REMOTE_ADDR': '127.0.0.1'}
        assert get_client_ip(req_direct) == '127.0.0.1'
        
    def test_track_changes(self, sample_data):
        """Test tracking changes between instances"""
        client, quotation = sample_data
        
        # Test client changes
        new_client = Client(
            client_name="New Name",
            company_name="Test Company",
            email="test@example.com"
        )
        changes = track_client_changes(client, new_client)
        assert 'client_name' in changes
        assert changes['client_name']['old'] == 'Test Client'
        assert changes['client_name']['new'] == 'New Name'
        
        # Test quotation changes
        new_quotation = Quotation(
            client=quotation.client,
            validity_period=60,
            point_of_contact="Test POC"
        )
        changes = track_quotation_changes(quotation, new_quotation)
        assert 'validity_period' in changes
        assert changes['validity_period']['old'] == '30'
        assert changes['validity_period']['new'] == '60'

@patch('quotations.services.email_service.EmailMessage')
@pytest.mark.django_db
def test_send_email(mock_email_message, sample_data):
    """Test email sending"""
    client, quotation = sample_data
    
    # Setup mock email instance
    mock_email_instance = MagicMock()
    mock_email_message.return_value = mock_email_instance
    
    # Test successful send
    send_quotation_email(quotation)
    
    mock_email_message.assert_called_once()
    call_args = mock_email_message.call_args[1]
    assert call_args['to'] == ['test@example.com']
    assert "Quotation" in call_args['subject']
    mock_email_instance.send.assert_called_once()
    
    # Test with attachments
    with patch('quotations.services.email_service.os.path.exists', return_value=True):
        send_quotation_email(quotation, docx_path='test.docx', pdf_path='test.pdf')
        assert mock_email_instance.attach_file.call_count == 2
