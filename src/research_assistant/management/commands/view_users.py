# src/research_assistant/management/commands/view_users.py

# python manage.py view_users

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'View all users in the database'

    def handle(self, *args, **options):
        self.stdout.write('Fetching users from database...')
        
        # Get all users
        users = User.objects.all().order_by('date_joined')
        
        if not users:
            self.stdout.write(self.style.WARNING('No users found in database'))
            return

        self.stdout.write('\nUser List:')
        self.stdout.write('-' * 50)
        
        for user in users:
            self.stdout.write(f'\nUser ID: {user.id}')
            self.stdout.write(f'Email: {user.email}')
            self.stdout.write(f'Full Name: {user.first_name} {user.last_name}')
            self.stdout.write(f'Last Login: {user.last_login or "Never"}')
            self.stdout.write(f'Date Joined: {user.date_joined}')
            self.stdout.write(f'Is Active: {user.is_active}')
            self.stdout.write(f'Is Staff: {user.is_staff}')
            self.stdout.write('-' * 50)

        self.stdout.write(self.style.SUCCESS(f'\nTotal Users: {users.count()}'))