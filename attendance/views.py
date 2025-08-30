import logging
import json
import uuid
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from .serializers import (
    MarkAttendanceSerializer,
    QRCodeScanSerializer,
    HealthCheckSerializer
)
from .throttling import AttendanceRateThrottle
from .jwt_utils import JWTService
from .models import AttendanceRecord

logger = logging.getLogger(__name__)

class MarkAttendanceView(APIView):
    """
    API endpoint for marking attendance from Educate App.
    Records attendance locally and forwards to SPOC portal.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [AttendanceRateThrottle]
    
    def post(self, request, *args, **kwargs):
        # Get student_external_id from request data or user profile
        data = request.data.copy()
        
        # Extract token from Authorization header if not in request data
        if 'token' not in data and 'HTTP_AUTHORIZATION' in request.META:
            auth_header = request.META['HTTP_AUTHORIZATION'].split()
            if len(auth_header) == 2 and auth_header[0].lower() == 'bearer':
                data['token'] = auth_header[1]
        
        # If student_external_id is not in request data, try to get it from user profile
        if 'student_external_id' not in data or not data['student_external_id']:
            if not request.user.student_external_id:
                return Response(
                    {"error": "Student external ID is required and not found in user profile"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            data['student_external_id'] = request.user.student_external_id
        
        # Add user to context for logging and validation
        context = {'request': request, 'user': request.user}
        
        try:
            serializer = MarkAttendanceSerializer(data=data, context=context)
            if not serializer.is_valid():
                logger.warning(f"Attendance validation failed: {serializer.errors}")
                return Response(
                    {
                        "status": "error",
                        "message": "Invalid data provided",
                        "errors": serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Check for existing attendance record
            existing_record = AttendanceRecord.objects.filter(
                external_session_id=serializer.validated_data['session_id'],
                student_external_id=data['student_external_id']
            ).first()
            
            if existing_record:
                return Response(
                    {
                        "status": "success",
                        "message": "Attendance already recorded",
                        "attendance_id": str(existing_record.id),
                        "marked_at": existing_record.marked_at.isoformat(),
                        "synced_with_spoc": existing_record.synced_with_spoc
                    },
                    status=status.HTTP_200_OK
                )
            
            # Create new attendance record
            attendance = serializer.save()
            
            # Log successful attendance creation
            logger.info(
                f"Attendance recorded - Session: {attendance.external_session_id}, "
                f"Student: {attendance.student_external_id}, "
                f"User: {request.user.email}"
            )
            
            # Forward to SPOC server asynchronously
            push_mark_to_spoc.delay(
                session_id=str(attendance.external_session_id),
                student_external_id=attendance.student_external_id,
                token=attendance.token,
                method=attendance.method
            )
            
            return Response(
                {
                    "status": "success",
                    "message": "Attendance recorded successfully",
                    "data": MarkAttendanceSerializer(attendance).data
                }, 
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Error creating attendance record: {str(e)}", exc_info=True)
            return Response(
                {
                    "status": "error",
                    "message": "Failed to create attendance record",
                    "error": str(e)
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QRCodeScanView(APIView):
    """
    Handle QR code scanning from Educate Portal
    Validates the QR code and returns session information
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [AttendanceRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = QRCodeScanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        qr_data = serializer.validated_data['qr_data']
        
        try:
            # Extract token from QR code data
            # QR data format: {"session_id": "...", "token": "..."}
            try:
                qr_content = json.loads(qr_data)
                session_id = qr_content.get('session_id')
                token = qr_content.get('token')
                
                if not all([session_id, token]):
                    raise ValidationError('Invalid QR code format')
                    
            except (json.JSONDecodeError, AttributeError):
                raise ValidationError('Invalid QR code data')
            
            # Verify the JWT token
            payload = JWTService.verify_token(token)
            
            # Verify session_id matches
            if payload.get('session_id') != session_id:
                raise AuthenticationFailed('Invalid session ID in QR code')
            
            # Check if attendance is already marked
            if AttendanceRecord.objects.filter(
                external_session_id=session_id,
                student=request.user
            ).exists():
                return Response({
                    'status': 'already_marked',
                    'message': 'Attendance already marked for this session',
                    'session_id': session_id,
                    'course_id': payload.get('course_id')
                }, status=status.HTTP_200_OK)
            
            # Return session info for confirmation
            return Response({
                'status': 'valid',
                'session': {
                    'id': session_id,
                    'course_id': payload.get('course_id'),
                    'teacher_id': payload.get('teacher_id'),
                    'expires_in': (datetime.fromtimestamp(payload['exp']) - datetime.utcnow()).total_seconds()
                }
            })
            
        except Exception as e:
            logger.error(f'QR code validation failed: {str(e)}')
            raise ValidationError('Invalid or expired QR code')


class MarkAttendanceView(APIView):
    """
    Mark attendance after QR code validation
    This is called after the QR code is validated by QRCodeScanView
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [AttendanceRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = MarkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        session_id = serializer.validated_data['session_id']
        token = serializer.validated_data['token']
        
        try:
            # Verify the token again for security
            payload = JWTService.verify_token(token)
            
            # Verify session_id matches
            if payload.get('session_id') != session_id:
                raise ValidationError('Invalid session ID')
            
            # Check if attendance already marked (double-check)
            if AttendanceRecord.objects.filter(
                external_session_id=session_id,
                student=request.user
            ).exists():
                return Response({
                    'status': 'already_marked',
                    'message': 'Attendance already recorded for this session',
                    'session_id': session_id,
                    'course_id': payload.get('course_id')
                }, status=status.HTTP_200_OK)
            
            # Create attendance record
            attendance = AttendanceRecord.objects.create(
                external_session_id=session_id,
                student=request.user,
                method='QR',
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=self.get_client_ip(request),
                metadata={
                    'course_id': payload.get('course_id'),
                    'teacher_id': payload.get('teacher_id'),
                    'scanned_at': timezone.now().isoformat()
                }
            )
            
            # You can add additional logic here, like:
            # - Sending notifications
            # - Updating attendance statistics
            # - Triggering webhooks
            
            return Response({
                'status': 'success',
                'data': {
                    'attendance_id': str(attendance.id),
                    'session_id': session_id,
                    'course_id': payload.get('course_id'),
                    'marked_at': attendance.marked_at.isoformat(),
                    'expires_at': datetime.fromtimestamp(payload['exp']).isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"Error marking attendance: {str(e)}")
            raise ValidationError('Failed to mark attendance. Please try again.')
    
    def get_client_ip(self, request):
        """Get the client's IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class HealthCheckView(APIView):
    """
    Simple health check endpoint.
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        return Response({
            'status': 'ok',
            'timestamp': timezone.now().isoformat(),
            'service': 'attendance'
        })
