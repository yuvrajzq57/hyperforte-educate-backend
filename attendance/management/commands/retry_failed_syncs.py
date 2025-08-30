import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from ...models import AttendanceRecord
from ...tasks import push_mark_to_spoc

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Retry failed attendance syncs with SPOC server'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Number of hours to look back for failed syncs (default: 24)'
        )
        parser.add_argument(
            '--max-retries',
            type=int,
            default=3,
            help='Maximum number of times to retry a failed sync (default: 3)'
        )
    
    def handle(self, *args, **options):
        hours = options['hours']
        max_retries = options['max_retries']
        
        # Calculate the time threshold for failed syncs
        time_threshold = timezone.now() - timedelta(hours=hours)
        
        # Get failed syncs that haven't exceeded max retries
        failed_syncs = AttendanceRecord.objects.filter(
            synced_with_spoc=False,
            marked_at__gte=time_threshold
        )
        
        self.stdout.write(f'Found {failed_syncs.count()} failed syncs to retry...')
        
        success_count = 0
        for record in failed_syncs:
            try:
                # Check if we've exceeded max retries
                if record.sync_error and record.sync_error.count('Retry') >= max_retries:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Skipping record {record.id} - exceeded max retries ({max_retries})'
                        )
                    )
                    continue
                
                # Queue the task for retry
                push_mark_to_spoc.delay(
                    session_id=str(record.external_session_id),
                    student_external_id=record.student_external_id,
                    token='',  # Token might be expired, will need to be handled in the task
                    method=record.method
                )
                
                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Queued retry for record {record.id} (Session: {record.external_session_id})'
                    )
                )
                
            except Exception as e:
                error_msg = f'Error queuing retry for record {record.id}: {str(e)}'
                logger.error(error_msg)
                self.stderr.write(self.style.ERROR(error_msg))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully queued {success_count} failed syncs for retry.'
            )
        )
