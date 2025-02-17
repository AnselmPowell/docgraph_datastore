# src/research_assistant/management/commands/add_test_user.py

# python manage.py add_test_user


from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import IntegrityError

class Command(BaseCommand):
    help = 'Add a test user to the database'

    def handle(self, *args, **options):
        self.stdout.write('Starting user creation process...')
        
        # User details
        email = 'Sanyu98@example.com'
        password = 'TestPass123!'  # In production, this should be more secure
        first_name = 'Sanyu'
        last_name = 'Everline'
        
            
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.ERROR(f'Email {email} already exists'))
            return

        # Validate email format
        if '@' not in email or '.' not in email:
            self.stdout.write(self.style.ERROR('Invalid email format'))
            return

        # Validate password
        if len(password) < 8:
            self.stdout.write(self.style.ERROR('Password must be at least 8 characters'))
            return

        # Create user
        self.stdout.write('Creating user...')
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        self.stdout.write('User details:')
        self.stdout.write(f'Email: {user.email}')
        self.stdout.write(f'Full Name: {user.first_name} {user.last_name}')
        
        self.stdout.write(self.style.SUCCESS('User created successfully'))