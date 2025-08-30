from django.db import models
from django.conf import settings
from django.utils import timezone

class AttendanceRecord(models.Model):
    """
    Model to track student attendance records.
    """
    ATTENDANCE_METHODS = (
        ('QR', 'QR Code'),
        ('MANUAL', 'Manual Entry'),
        ('AUTO', 'Automatic')
    )
    
    ATTENDANCE_STATUS = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused')
    )

    external_session_id = models.UUIDField(
        db_index=True,
        help_text="External session identifier from the QR code"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        help_text="Student who marked the attendance"
    )
    student_external_id = models.CharField(
        max_length=255,
        db_index=True,
        null=True,
        blank=True,
        help_text="External ID of the student (from SPOC server)"
    )
    marked_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the attendance was marked"
    )
    status = models.CharField(
        max_length=10,
        choices=ATTENDANCE_STATUS,
        default='present',
        help_text="Attendance status (present/absent/late/excused)"
    )
    method = models.CharField(
        max_length=10,
        choices=ATTENDANCE_METHODS,
        default='QR',
        help_text="How the attendance was marked"
    )
    source = models.CharField(
        max_length=50,
        default='EDUCATE',
        help_text="Source system where attendance was marked"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent of the device that marked attendance"
    )
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        help_text="IP address of the device that marked attendance"
    )
    synced_with_spoc = models.BooleanField(
        default=False,
        help_text="Whether the record was synced with the SPOC server"
    )
    sync_error = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if sync with SPOC server failed"
    )
    last_sync_attempt = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the last sync attempt was made"
    )

    class Meta:
        verbose_name = "Attendance Record"
        verbose_name_plural = "Attendance Records"
        unique_together = (('external_session_id', 'student'),)
        indexes = [
            models.Index(fields=['student', 'external_session_id']),
            models.Index(fields=['marked_at']),
            models.Index(fields=['student_external_id']),
            models.Index(fields=['synced_with_spoc']),
            models.Index(fields=['status']),
        ]
        ordering = ['-marked_at']

    def __str__(self):
        return f"{self.student.email} - {self.external_session_id} - {self.status.upper()} at {self.marked_at}"
    
    def mark_synced(self, success=True, error_message=None):
        """
        Mark the record as synced with the SPOC server.
        
        Args:
            success (bool): Whether the sync was successful
            error_message (str, optional): Error message if sync failed
        """
        self.synced_with_spoc = success
        self.sync_error = error_message if not success else None
        self.last_sync_attempt = timezone.now()
        self.save(update_fields=[
            'synced_with_spoc', 
            'sync_error', 
            'last_sync_attempt'
        ])
