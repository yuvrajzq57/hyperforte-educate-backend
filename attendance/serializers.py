from rest_framework import serializers
import uuid
import json
from django.utils import timezone
from django.core.exceptions import ValidationError

class MarkAttendanceSerializer(serializers.Serializer):
    """
    Serializer for marking attendance after QR code validation.
    """
    session_id = serializers.UUIDField(required=True)
    token = serializers.CharField(required=True, max_length=2000)
    
    def validate_session_id(self, value):
        """Validate session_id format."""
        if isinstance(value, str):
            try:
                return uuid.UUID(value)
            except ValueError:
                raise ValidationError("Invalid session_id format. Must be a valid UUID.")
        return value
    
    def validate(self, data):
        """Additional validation for the attendance data."""
        # You can add cross-field validation here if needed
        return data


class MarkAttendanceOutSerializer(serializers.Serializer):
    """Serializer for attendance marking response."""
    status = serializers.ChoiceField(choices=[('ok', 'OK'), ('already_marked', 'Already Marked')])
    session_id = serializers.UUIDField()


class QRCodeScanSerializer(serializers.Serializer):
    """
    Serializer for validating scanned QR code data.
    Expects a JSON string with session_id and token.
    """
    qr_data = serializers.CharField(required=True)
    
    def validate_qr_data(self, value):
        """Validate the QR code data format."""
        try:
            data = json.loads(value)
            if not all(key in data for key in ['session_id', 'token']):
                raise ValidationError('QR code data must contain session_id and token')
            return value
        except json.JSONDecodeError:
            raise ValidationError('Invalid QR code format. Expected valid JSON.')


class QRCodeValidationResponseSerializer(serializers.Serializer):
    """
    Serializer for QR code validation response.
    """
    status = serializers.ChoiceField(choices=[
        ('valid', 'Valid'),
        ('already_marked', 'Already Marked'),
        ('invalid', 'Invalid')
    ])
    message = serializers.CharField(required=False)
    session_id = serializers.UUIDField(required=False)
    course_id = serializers.UUIDField(required=False)
    
    class Meta:
        fields = ['status', 'message', 'session_id', 'course_id']


class AttendanceResponseSerializer(serializers.Serializer):
    """
    Serializer for attendance marking response.
    """
    status = serializers.ChoiceField(choices=[
        ('success', 'Success'),
        ('already_marked', 'Already Marked'),
        ('error', 'Error')
    ])
    data = serializers.DictField(required=False)
    message = serializers.CharField(required=False)
    
    class Meta:
        fields = ['status', 'data', 'message']


class ErrorResponseSerializer(serializers.Serializer):
    """
    Standard error response format.
    """
    error = serializers.DictField()
    status_code = serializers.IntegerField(required=False)
    
    class Meta:
        fields = ['error', 'status_code']


class HealthCheckSerializer(serializers.Serializer):
    """Serializer for health check endpoint."""
    status = serializers.ChoiceField(choices=[('ok', 'OK')])
    timestamp = serializers.DateTimeField()
    service = serializers.CharField()

    def to_representation(self, instance):
        """Format the health check response."""
        return {
            'status': 'ok',
            'timestamp': timezone.now().isoformat(),
            'service': 'attendance'
        }
