from django.contrib import admin
from .models import AttendanceRecord

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    """Admin interface for AttendanceRecord model."""
    list_display = (
        'external_session_id',
        'student_email',
        'marked_at',
        'method',
        'ip_address',
    )
    
    list_filter = ('method', 'marked_at')
    search_fields = (
        'student__email',
        'student__username',
        'external_session_id',
        'ip_address',
    )
    date_hierarchy = 'marked_at'
    readonly_fields = ('marked_at', 'user_agent')
    
    def student_email(self, obj):
        return obj.student.email
    student_email.short_description = 'Student Email'
    student_email.admin_order_field = 'student__email'
