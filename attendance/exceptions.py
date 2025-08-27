"""
Custom exception handlers for the attendance app.
"""
from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from jwt import PyJWTError
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler that formats all errors in a consistent way.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # If the exception is handled by DRF, format the response
    if response is not None:
        error_data = {
            'error': {
                'code': exc.get_codes() if hasattr(exc, 'get_codes') else 'error',
                'message': str(exc),
                'details': exc.get_full_details() if hasattr(exc, 'get_full_details') else {}
            }
        }
        return Response(error_data, status=response.status_code)
    
    # Handle specific exceptions
    if isinstance(exc, PyJWTError):
        error_data = {
            'error': {
                'code': 'invalid_token',
                'message': 'Invalid or expired token',
                'details': str(exc)
            }
        }
        return Response(error_data, status=status.HTTP_401_UNAUTHORIZED)
    
    if isinstance(exc, ValidationError):
        error_data = {
            'error': {
                'code': 'validation_error',
                'message': 'Invalid input data',
                'details': exc.message_dict if hasattr(exc, 'message_dict') else str(exc)
            }
        }
        return Response(error_data, status=status.HTTP_400_BAD_REQUEST)
    
    # Log unexpected errors
    logger.exception("Unhandled exception occurred")
    
    # Default error response for unhandled exceptions
    error_data = {
        'error': {
            'code': 'server_error',
            'message': 'An unexpected error occurred',
            'details': str(exc) if str(exc) else 'No additional details available'
        }
    }
    
    return Response(error_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
