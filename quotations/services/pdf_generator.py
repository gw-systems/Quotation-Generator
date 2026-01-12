"""
PDF generation service using LibreOffice headless conversion
"""
import os
import subprocess
from django.conf import settings


class QuotationPdfGenerator:
    """Generate PDF quotations from DOCX files"""
    
    def __init__(self, docx_path):
        """
        Initialize generator with DOCX file path
        
        Args:
            docx_path: Path to DOCX file to convert
        """
        self.docx_path = docx_path
        
    def generate(self, output_dir=None):
        """
        Generate PDF from DOCX using LibreOffice headless
        
        Args:
            output_dir: Optional custom output directory
            
        Returns:
            str: Path to generated PDF file
        """
        if not output_dir:
            output_dir = os.path.join(settings.MEDIA_ROOT, 'quotations', 'pdf')
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Try to convert using LibreOffice
        try:
            # Common LibreOffice paths on Windows
            libreoffice_paths = [
                r'C:\Program Files\LibreOffice\program\soffice.exe',
                r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
                r'soffice',  # If in PATH
            ]
            
            libreoffice_exe = None
            for path in libreoffice_paths:
                if os.path.exists(path) or path == 'soffice':
                    libreoffice_exe = path
                    break
            
            if not libreoffice_exe:
                raise FileNotFoundError("LibreOffice not found. Please install LibreOffice.")
            
            # Run conversion command
            command = [
                libreoffice_exe,
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', output_dir,
                self.docx_path
            ]
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise Exception(f"LibreOffice conversion failed: {result.stderr}")
            
            # Determine output PDF path
            docx_filename = os.path.basename(self.docx_path)
            pdf_filename = os.path.splitext(docx_filename)[0] + '.pdf'
            pdf_path = os.path.join(output_dir, pdf_filename)
            
            if not os.path.exists(pdf_path):
                raise Exception(f"PDF file was not created: {pdf_path}")
            
            return pdf_path
            
        except FileNotFoundError:
            raise Exception(
                "LibreOffice is not installed or not found. "
                "Please install LibreOffice from https://www.libreoffice.org/"
            )
        except subprocess.TimeoutExpired:
            raise Exception("PDF conversion timed out")
        except Exception as e:
            raise Exception(f"PDF generation failed: {str(e)}")


def generate_quotation_pdf(docx_path):
    """
    Helper function to generate PDF from DOCX
    
    Args:
        docx_path: Path to DOCX file
        
    Returns:
        str: Path to generated PDF file
    """
    generator = QuotationPdfGenerator(docx_path)
    return generator.generate()


def generate_quotation_pdf_from_quotation(quotation):
    """
    Generate PDF directly from quotation (generates DOCX first)
    
    Args:
        quotation: Quotation model instance
        
    Returns:
        str: Path to generated PDF file
    """
    from .document_generator import generate_quotation_docx
    
    # First generate DOCX
    docx_path = generate_quotation_docx(quotation)
    
    # Then convert to PDF
    pdf_path = generate_quotation_pdf(docx_path)
    
    return pdf_path
