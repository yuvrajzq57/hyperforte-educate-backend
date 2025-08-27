from django.db import models
from django.conf import settings
from django.utils import timezone

class AttendanceRecord(models.Model):
    ATTENDANCE_METHODS = (
        ('QR', 'QR Code'),
        ('CODE', 'Manual Code'),
        ('MANUAL', 'Manual Entry')
    )

    external_session_id = models.UUIDField(db_index=True)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    marked_at = models.DateTimeField(auto_now_add=True)
    method = models.CharField(
        max_length=10,
        choices=ATTENDANCE_METHODS,
        default='QR'
    )
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        unique_together = (('external_session_id', 'student'),)
        indexes = [
            models.Index(fields=['student', 'external_session_id']),
            models.Index(fields=['marked_at']),
        ]
        ordering = ['-marked_at']

    def __str__(self):
        return f"{self.student.email} - {self.external_session_id} - {self.marked_at}"
