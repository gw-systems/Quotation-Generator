"""
Management command to set or update user email addresses
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


class Command(BaseCommand):
    help = 'Set or update email address for a user'

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            type=str,
            help='Username of the user to update'
        )
        parser.add_argument(
            'email',
            type=str,
            help='Email address to set for the user'
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            self.stdout.write(self.style.ERROR(f'Invalid email address: {email}'))
            return
        
        # Find user
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User not found: {username}'))
            self.stdout.write('\nAvailable users:')
            for u in User.objects.all():
                self.stdout.write(f'  - {u.username}')
            return
        
        # Store old email
        old_email = user.email or '(not set)'
        
        # Update email
        user.email = email
        user.save()
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Email updated for user: {username}'))
        self.stdout.write(f'  Old email: {old_email}')
        self.stdout.write(f'  New email: {email}')
        self.stdout.write('')
        self.stdout.write('User can now send quotations from this email address.')
