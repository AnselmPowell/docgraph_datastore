from django.core.management.base import BaseCommand
from django.utils import timezone
from research_assistant.models import DocumentMetadata

class Command(BaseCommand):
    help = 'Delete documents and related data older than 30 days'

    def handle(self, *args, **kwargs):
        try:
            count = DocumentMetadata.delete_expired()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {count} expired documents')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error deleting expired documents: {str(e)}')
            )