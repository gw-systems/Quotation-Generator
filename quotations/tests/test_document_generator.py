
import pytest
from unittest.mock import MagicMock, patch, mock_open
from quotations.services.document_generator import QuotationDocxGenerator, generate_quotation_docx
from quotations.models import Quotation, Client, QuotationLocation, QuotationItem

@pytest.fixture
def sample_quotation(db):
    client = Client.objects.create(
        client_name="Test Client",
        company_name="Test Company",
        email="test@example.com",
        contact_number="1234567890",
        address="Test Address"
    )
    quotation = Quotation.objects.create(
        client=client,
        point_of_contact="Test POC",
        validity_period=30
    )
    
    # Create locations and items
    loc1 = QuotationLocation.objects.create(
        quotation=quotation,
        location_name="Loc 1",
        order=0
    )
    QuotationItem.objects.create(
        location=loc1,
        item_description="storage_charges",
        unit_cost="100",
        quantity="5"
    )
    
    return quotation

@patch('quotations.services.document_generator.Document')
@patch('quotations.services.document_generator.os.makedirs')
def test_generate_document_structure(mock_makedirs, mock_document, sample_quotation):
    """Test that document generation calls the right methods and structure"""
    # Setup mock document
    mock_doc_instance = MagicMock()
    mock_document.return_value = mock_doc_instance
    
    # Mock tables
    mock_table_client = MagicMock()
    mock_table_summary = MagicMock()
    mock_table_pricing = MagicMock() # Table 2 (pricing)
    
    # Setup table rows/cells structure
    def create_mock_row():
        row = MagicMock()
        row.cells = [MagicMock() for _ in range(4)]
        return row
        
    mock_table_client.rows = [create_mock_row() for _ in range(3)]
    mock_table_summary.rows = [create_mock_row() for _ in range(2)]
    
    # Setup pricing table with columns
    mock_table_pricing.columns = [MagicMock() for _ in range(4)]
    mock_table_pricing.rows = [create_mock_row() for _ in range(10)]
    
    # Assign tables to doc
    mock_doc_instance.tables = [mock_table_client, mock_table_summary, mock_table_pricing]
    
    # Mock paragraphs
    mock_para = MagicMock()
    mock_para.text = "PRICING DETAILS"
    mock_doc_instance.paragraphs = [mock_para]
    
    # Mock XML element parent/child for table logic
    mock_table_element = mock_table_pricing._element
    mock_parent = MagicMock()
    mock_table_element.getparent.return_value = mock_parent
    # When list(parent) is called, it iterates. We need it to contain our table element.
    mock_parent.__iter__.return_value = iter([mock_table_element])
    # Also need index to work
    mock_parent.index.side_effect = lambda x: 0 if x == mock_table_element else -1
    
    # Run generator
    generator = QuotationDocxGenerator(sample_quotation)
    output_path = generator.generate()
    
    # Verify Document was initialized
    mock_document.assert_called_once()
    
    # Verify save was called
    mock_doc_instance.save.assert_called()
    assert output_path.endswith('.docx')

@patch('quotations.services.document_generator.Document')
def test_populate_client_details(mock_document, sample_quotation):
    """Test client details population"""
    mock_doc_instance = MagicMock()
    mock_document.return_value = mock_doc_instance
    
    # Setup client table (Table 0)
    mock_table = MagicMock()
    # Need specific cells to be accessible
    row0 = MagicMock(); row0.cells = [MagicMock(), MagicMock()]
    row1 = MagicMock(); row1.cells = [MagicMock(), MagicMock()]
    row2 = MagicMock(); row2.cells = [MagicMock(), MagicMock()]
    mock_table.rows = [row0, row1, row2]
    
    mock_doc_instance.tables = [mock_table]
    
    generator = QuotationDocxGenerator(sample_quotation)
    generator._populate_client_details(mock_doc_instance)
    
    # Check if proper usage was made
    assert "Test Client" in row0.cells[0].text
    assert "Test Company" in row0.cells[1].text
    assert "test@example.com" in row1.cells[0].text

@patch('quotations.services.document_generator.Document')
def test_populate_quotation_summary(mock_document, sample_quotation):
    """Test quotation summary population"""
    mock_doc_instance = MagicMock()
    mock_document.return_value = mock_doc_instance
    
    # Setup tables
    mock_table_dummy = MagicMock()
    mock_table_summary = MagicMock()
    
    row0 = MagicMock(); row0.cells = [MagicMock()]
    row1 = MagicMock(); row1.cells = [MagicMock(), MagicMock()]
    mock_table_summary.rows = [row0, row1]
    
    mock_doc_instance.tables = [mock_table_dummy, mock_table_summary]
    
    generator = QuotationDocxGenerator(sample_quotation)
    generator._populate_quotation_summary(mock_doc_instance)
    
    assert str(sample_quotation.date.strftime('%d-%m-%Y')) in row0.cells[0].text
    assert "30 days" in row1.cells[0].text
    assert "Test POC" in row1.cells[1].text

def test_helper_function(sample_quotation):
    """Test the helper wrapper function"""
    with patch('quotations.services.document_generator.QuotationDocxGenerator') as MockGen:
        instance = MockGen.return_value
        instance.generate.return_value = "path/to/doc.docx"
        
        result = generate_quotation_docx(sample_quotation)
        
        MockGen.assert_called_once_with(sample_quotation)
        instance.generate.assert_called_once()
        assert result == "path/to/doc.docx"
