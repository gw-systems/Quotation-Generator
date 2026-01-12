"""
Email service for sending quotations (deferred implementation)
"""
from django.core.mail import EmailMessage
from django.conf import settings
import os


def send_quotation_email(quotation, recipient_email=None, docx_path=None, pdf_path=None, cc_emails=None):
    """
    Send quotation via email
    
    Args:
        quotation: Quotation model instance
        recipient_email: Email address to send to (defaults to client email)
        docx_path: Path to DOCX file (optional)
        pdf_path: Path to PDF file (optional)
        cc_emails: List of CC email addresses (optional)
        
    Returns:
        bool: True if sent successfully
    """
    # Default to client email if not specified
    if not recipient_email:
        recipient_email = quotation.client.email
    
    # Email subject and body
    subject = f"Quotation {quotation.quotation_number} from Godamwale"
    
    body = f"""
Dear {quotation.client.client_name},

Thank you for your interest in Godamwale's Comprehensive Warehousing & Logistics Services.

Please find attached the quotation ({quotation.quotation_number}) as requested.

Quotation Details:
- Quotation Number: {quotation.quotation_number}
- Date: {quotation.date.strftime('%d %B %Y')}
- Valid Until: {quotation.validity_date.strftime('%d %B %Y')}
- Grand Total: ₹ {quotation.grand_total:,.2f}

For any questions or clarifications, please feel free to contact {quotation.point_of_contact}.

Thank you for considering Godamwale as your warehousing partner.

Best regards,
Godamwale Team
    """.strip()
    
    # Create email
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@godamwale.com',
        to=[recipient_email],
        cc=cc_emails or [],
    )
    
    # Attach files if provided
    if docx_path and os.path.exists(docx_path):
        email.attach_file(docx_path)
    
    if pdf_path and os.path.exists(pdf_path):
        email.attach_file(pdf_path)
    
    # Send email
    try:
        email.send()
        return True
    except Exception as e:
        # Log error (in production, use proper logging)
        print(f"Failed to send email: {str(e)}")
        return False
