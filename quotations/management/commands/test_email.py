"""
Management command to test email configuration
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Test email configuration by sending a test email'

    def add_arguments(self, parser):
        parser.add_argument(
            'recipient',
            type=str,
            help='Email address to send test email to'
        )
        parser.add_argument(
            '--from-email',
            type=str,
            default=None,
            help='Optional: sender email address (defaults to DEFAULT_FROM_EMAIL)'
        )

    def handle(self, *args, **options):
        recipient = options['recipient']
        from_email = options.get('from_email') or settings.DEFAULT_FROM_EMAIL
        
        self.stdout.write(self.style.WARNING(f'\nTesting email configuration...'))
        self.stdout.write(f'From: {from_email}')
        self.stdout.write(f'To: {recipient}')
        self.stdout.write(f'SMTP Host: {settings.EMAIL_HOST}')
        self.stdout.write(f'SMTP Port: {settings.EMAIL_PORT}')
        self.stdout.write(f'TLS Enabled: {settings.EMAIL_USE_TLS}')
        self.stdout.write('')
        
        try:
            send_mail(
                subject='Test Email from Quotation Builder',
                message='This is a test email from the Godamwale Quotation Builder system.\n\nIf you received this email, your email configuration is working correctly!',
                from_email=from_email,
                recipient_list=[recipient],
                fail_silently=False,
            )
            
            self.stdout.write(self.style.SUCCESS(f'\n✓ Test email sent successfully to {recipient}'))
            self.stdout.write(self.style.SUCCESS('Please check the inbox to confirm delivery.'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Failed to send test email'))
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('Common issues:'))
            self.stdout.write('1. Check that EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are set in .env')
            self.stdout.write('2. For Gmail, ensure you are using an App Password, not your regular password')
            self.stdout.write('3. Check that EMAIL_HOST and EMAIL_PORT are correct')
            self.stdout.write('4. Verify your firewall allows outgoing connections on port 587')
