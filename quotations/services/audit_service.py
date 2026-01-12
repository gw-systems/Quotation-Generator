"""
Audit trail service for tracking quotation actions
"""
from django.contrib.auth.models import User
from ..models import QuotationAudit


def log_quotation_action(quotation, action, user=None, changes=None, ip_address=None, metadata=None):
    """
    Log a quotation action to the audit trail
    
    Args:
        quotation: Quotation model instance
        action: Action type (from QuotationAudit.ACTION_CHOICES)
        user: User who performed the action (optional)
        changes: Dictionary of changes (optional)
        ip_address: IP address of user (optional)
        metadata: Additional metadata dictionary (optional)
        
    Returns:
        QuotationAudit: Created audit log instance
    """
    audit_log = QuotationAudit.objects.create(
        quotation=quotation,
        action=action,
        user=user,
        changes=changes or {},
        ip_address=ip_address,
        additional_metadata=metadata or {}
    )
    return audit_log


def get_client_ip(request):
    """
    Extract client IP address from request
    
    Args:
        request: Django request object
        
    Returns:
        str: IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def track_quotation_changes(old_instance, new_instance):
    """
    Track changes between two quotation instances
    
    Args:
        old_instance: Previous quotation state
        new_instance: New quotation state
        
    Returns:
        dict: Dictionary of field changes
    """
    changes = {}
    
    # Fields to track
    tracked_fields = [
        'client', 'validity_period', 'point_of_contact', 'status'
    ]
    
    for field in tracked_fields:
        old_value = getattr(old_instance, field, None)
        new_value = getattr(new_instance, field, None)
        
        if old_value != new_value:
            changes[field] = {
                'old': str(old_value),
                'new': str(new_value)
            }
    
    return changes
