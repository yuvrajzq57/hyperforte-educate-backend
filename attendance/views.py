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
from rest_framework.authentication import TokenAuthentication, BaseAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed, ValidationError

class DebugJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        logger.debug("Attempting JWT Authentication")
        try:
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            logger.debug(f"JWT Auth Header: {auth_header}")
            
            if not auth_header.startswith('Bearer '):
                logger.debug("No Bearer token in header")
                return None
                
            user_jwt = super().authenticate(request)
            if user_jwt is not None:
                logger.debug(f"JWT Authentication successful for user: {user_jwt[0].username}")
            else:
                logger.debug("JWT Authentication failed - no user returned")
            return user_jwt
        except Exception as e:
            logger.error(f"JWT Authentication error: {str(e)}", exc_info=True)
            return None

class DebugTokenAuthentication(TokenAuthentication):
    def authenticate(self, request):
        logger.debug("Attempting Token Authentication")
        try:
            result = super().authenticate(request)
            if result is not None:
                logger.debug(f"Token Authentication successful for user: {result[0].username}")
            else:
                logger.debug("Token Authentication failed - no user returned")
            return result
        except Exception as e:
            logger.error(f"Token Authentication error: {str(e)}", exc_info=True)
            return None
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
    authentication_classes = [DebugJWTAuthentication, DebugTokenAuthentication]  # Debug versions of auth classes
    permission_classes = [IsAuthenticated]
    throttle_classes = [AttendanceRateThrottle]
    
    def post(self, request, *args, **kwargs):
        # Add debug logging for the incoming request
        logger.debug(
            f"MarkAttendanceView - Request received. "
            f"User: {request.user.id if request.user.is_authenticated else 'Not authenticated'}, "
            f"Auth headers: {request.META.get('HTTP_AUTHORIZATION', 'No auth header')}, "
            f"Data: {request.data}"
        )
        
        # Log authentication classes being used
        logger.debug(f"Authentication classes: {[auth.__name__ for auth in self.authentication_classes]}")
        
        # If not authenticated, log why
        if not request.user.is_authenticated:
            logger.warning("User not authenticated. Available auth headers: %s", 
                         {k: v for k, v in request.META.items() if k.startswith('HTTP_')})
        
        # Get student_external_id from request data or user profile
        data = request.data.copy()
        
        # Extract token from Authorization header if not in request data
        if 'token' not in data and 'HTTP_AUTHORIZATION' in request.META:
            auth_header = request.META['HTTP_AUTHORIZATION'].split()
            if len(auth_header) == 2 and auth_header[0].lower() == 'bearer':
                data['token'] = auth_header[1]
        
        # If student_external_id is not in request data, try to get it from user profile
        if 'student_external_id' not in data or not data['student_external_id']:
            if not hasattr(request.user, 'student_external_id') or not request.user.student_external_id:
                error_details = {
                    "status": "error",
                    "message": "Student external ID not found in user profile",
                    "details": {
                        "user_authenticated": request.user.is_authenticated,
                        "user_id": str(request.user.id) if request.user.is_authenticated else None,
                        "email": request.user.email if request.user.is_authenticated else None,
                        "has_student_external_id": hasattr(request.user, 'student_external_id'),
                        "student_external_id": getattr(request.user, 'student_external_id', None)
                    },
                    "solution": [
                        "1. Ensure the user is logged in with a valid student account",
                        "2. Check that the user's profile has a student_external_id set",
                        "3. If this is a test account, make sure it's properly configured with a student_external_id"
                    ]
                }
                logger.error(f"Student external ID not found: {error_details}")
                return Response(error_details, status=status.HTTP_400_BAD_REQUEST)
            
            logger.debug(f"Using student_external_id from user profile: {request.user.student_external_id}")
            data['student_external_id'] = request.user.student_external_id
        else:
            logger.debug(f"Using student_external_id from request: {data['student_external_id']}")
            
        logger.debug(f"Proceeding with student_external_id: {data['student_external_id']}")
        
        # Add user to context for logging and validation
        context = {'request': request, 'user': request.user}
        
        # Add debug information to response
        debug_info = {
            'user': {
                'id': str(request.user.id) if request.user.is_authenticated else None,
                'email': request.user.email if request.user.is_authenticated else None,
                'username': request.user.username if request.user.is_authenticated else None,
                'has_student_external_id': hasattr(request.user, 'student_external_id'),
                'student_external_id': getattr(request.user, 'student_external_id', None)
            },
            'request_data': data
        }
        
        try:
            serializer = MarkAttendanceSerializer(data=data, context=context)
            if not serializer.is_valid():
                logger.warning(f"Attendance validation failed: {serializer.errors}")
                return Response(
                    {
                        "status": "error",
                        "message": "Invalid data provided",
                        "errors": serializer.errors,
                        "debug": debug_info  # Include debug info in the response
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
    authentication_classes = [DebugJWTAuthentication, DebugTokenAuthentication]  # Debug versions of auth classes
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
