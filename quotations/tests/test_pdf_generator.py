
import pytest
import os
import subprocess
from unittest.mock import MagicMock, patch
from quotations.services.pdf_generator import QuotationPdfGenerator, generate_quotation_pdf

@patch('quotations.services.pdf_generator.subprocess.run')
@patch('quotations.services.pdf_generator.os.path.exists')
@patch('quotations.services.pdf_generator.os.makedirs')
def test_pdf_generation_success(mock_run, mock_exists, mock_makedirs):
    """Test successful PDF generation"""
    # Simulate LibreOffice existing (first call) and PDF output existing (second call)
    mock_exists.side_effect = [True, True]
    
    mock_run.return_value = MagicMock(returncode=0)
    
    generator = QuotationPdfGenerator("test.docx")
    pdf_path = generator.generate("output/dir")
    
    # Verify mkdirs called
    mock_makedirs.assert_called_with("output/dir", exist_ok=True)
    
    assert pdf_path.endswith('.pdf')
    mock_run.assert_called_once()
    assert "soffice" in mock_run.call_args[0][0][0] or "libreoffice" in mock_run.call_args[0][0][0].lower()

@patch('quotations.services.pdf_generator.subprocess.run')
@patch('quotations.services.pdf_generator.os.path.exists')
@patch('quotations.services.pdf_generator.os.makedirs')
def test_libreoffice_not_found(mock_makedirs, mock_exists, mock_run):
    """Test error when LibreOffice is not found"""
    # Simulate not found
    mock_exists.return_value = False
    
    generator = QuotationPdfGenerator("test.docx")
    
    # We expect mkdris to be called, then exists check
    with pytest.raises(Exception) as excinfo:
        generator.generate()
    
    assert "LibreOffice is not installed" in str(excinfo.value)

@patch('quotations.services.pdf_generator.subprocess.run')
@patch('quotations.services.pdf_generator.os.path.exists')
@patch('quotations.services.pdf_generator.os.makedirs')
def test_conversion_failure(mock_makedirs, mock_exists, mock_run):
    """Test failure during conversion process"""
    mock_exists.return_value = True # Exists
    mock_run.return_value = MagicMock(returncode=1, stderr="Conversion error")
    
    generator = QuotationPdfGenerator("test.docx")
    
    with pytest.raises(Exception) as excinfo:
        generator.generate()
    
    assert "LibreOffice conversion failed" in str(excinfo.value)
    
def test_helper_function():
    """Test helper wrapper"""
    with patch('quotations.services.pdf_generator.QuotationPdfGenerator') as MockGen:
        instance = MockGen.return_value
        instance.generate.return_value = "file.pdf"
        
        result = generate_quotation_pdf("file.docx")
        
        MockGen.assert_called_once_with("file.docx")
        assert result == "file.pdf"
