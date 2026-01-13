"""
Email service for sending quotations
"""
from django.core.mail import EmailMessage
from django.conf import settings
from django.core.exceptions import ValidationError
import os
import logging

logger = logging.getLogger(__name__)


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
        
    Raises:
        ValidationError: If sender has no email configured
    """
    # Default to client email if not specified
    if not recipient_email:
        recipient_email = quotation.client.email
    
    # Determine sender email (from quotation creator)
    sender_email = None
    sender_name = "Godamwale Team"
    
    if quotation.created_by and quotation.created_by.email:
        sender_email = quotation.created_by.email
        # Use creator's name if available
        if quotation.created_by.first_name or quotation.created_by.last_name:
            sender_name = f"{quotation.created_by.first_name} {quotation.created_by.last_name}".strip()
        else:
            sender_name = quotation.created_by.username
    else:
        # Fallback to default sender
        if hasattr(settings, 'DEFAULT_FROM_EMAIL') and settings.DEFAULT_FROM_EMAIL:
            sender_email = settings.DEFAULT_FROM_EMAIL
        else:
            error_msg = (
                f"Cannot send email: User '{quotation.created_by.username if quotation.created_by else 'Unknown'}' "
                "has no email address configured. Please set your email in your profile."
            )
            logger.error(error_msg)
            raise ValidationError(error_msg)
    
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
{sender_name}
Godamwale Team
    """.strip()
    
    # Create email
    from_email_formatted = f"{sender_name} <{sender_email}>"
    
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email_formatted,
        to=[recipient_email],
        cc=cc_emails or [],
        reply_to=[sender_email],  # Set reply-to to sender's email
    )
    
    # Attach files if provided
    if docx_path and os.path.exists(docx_path):
        email.attach_file(docx_path)
    
    if pdf_path and os.path.exists(pdf_path):
        email.attach_file(pdf_path)
    
    # Send email
    try:
        email.send()
        logger.info(f"Email sent successfully: {quotation.quotation_number} from {sender_email} to {recipient_email}")
        return True
    except Exception as e:
        # Log error
        logger.error(f"Failed to send email for {quotation.quotation_number}: {str(e)}")
        print(f"Failed to send email: {str(e)}")
        return False
