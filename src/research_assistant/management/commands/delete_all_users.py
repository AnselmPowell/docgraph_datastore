# src/research_assistant/management/commands/delete_all_users.py

# python manage.py delete_all_users
#  \\ Force deletion without confirmation:
# python manage.py delete_all_users --force

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import ProtectedError
from django.core.exceptions import ValidationError

class Command(BaseCommand):
    help = 'Delete all users from the database with confirmation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force deletion without confirmation',
        )

    def handle(self, *args, **options):
        self.stdout.write('\nStarting user deletion process...')
        
        # Get user count
        user_count = User.objects.count()
        
        if user_count == 0:
            self.stdout.write(self.style.WARNING('No users found in database'))
            return

        self.stdout.write(f'\nFound {user_count} users in database')
        self.stdout.write(self.style.WARNING('\nWARNING: This will delete all users!'))
        self.stdout.write(self.style.WARNING('This action cannot be undone!'))
        
        # Skip confirmation if --force flag is used
        if not options['force']:
            confirmation = input('\nType "DELETE" to confirm: ')
            
            if confirmation != 'DELETE':
                self.stdout.write(self.style.ERROR('\nDeletion cancelled'))
                return

        self.stdout.write('\nDeleting users...')
        
        # List users before deletion
        self.stdout.write('\nUsers to be deleted:')
        self.stdout.write('-' * 50)
        for user in User.objects.all():
            self.stdout.write(f'Email: {user.email} (ID: {user.id})')
        self.stdout.write('-' * 50)

        # Perform deletion
        deletion_count = 0
        error_count = 0
        error_list = []

        for user in User.objects.all():
            try:
                email = user.email
                user.delete()
                self.stdout.write(f'Deleted user: {email}')
                deletion_count += 1
                
            except ProtectedError as e:
                error_count += 1
                error_list.append(f"Could not delete {user.email}: Protected by related objects")
                self.stdout.write(self.style.ERROR(f'Protected Error for user {user.email}'))
                
            except ValidationError as e:
                error_count += 1
                error_list.append(f"Could not delete {user.email}: Validation error")
                self.stdout.write(self.style.ERROR(f'Validation Error for user {user.email}'))
                
            except Exception as e:
                error_count += 1
                error_list.append(f"Could not delete {user.email}: {str(e)}")
                self.stdout.write(self.style.ERROR(f'Unexpected Error for user {user.email}'))

        # Final report
        self.stdout.write('\nDeletion Summary:')
        self.stdout.write('-' * 50)
        self.stdout.write(f'Total users found: {user_count}')
        self.stdout.write(f'Successfully deleted: {deletion_count}')
        self.stdout.write(f'Failed deletions: {error_count}')
        
        if error_list:
            self.stdout.write('\nErrors encountered:')
            for error in error_list:
                self.stdout.write(self.style.ERROR(f'- {error}'))

        # Verify deletion
        remaining_users = User.objects.count()
        if remaining_users == 0:
            self.stdout.write(self.style.SUCCESS('\nAll users successfully deleted'))
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'\n{remaining_users} users remain in the database'
                )
            )