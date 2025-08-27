import jwt
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

class JWTService:
    @staticmethod
    def generate_qr_token(session_id, course_id, teacher_id):
        """
        Generate JWT token for QR code
        """
        payload = {
            "session_id": str(session_id),
            "course_id": str(course_id),
            "teacher_id": str(teacher_id),
            "exp": datetime.utcnow() + timedelta(minutes=settings.QR_CODE_EXPIRY_MINUTES),
            "iss": "spoc-dashboard",
            "aud": "educate-portal",
            "iat": datetime.utcnow()
        }
        return jwt.encode(
            payload, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def verify_token(token):
        """
        Verify JWT token and return payload if valid
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                audience="educate-portal",
                issuer="spoc-dashboard"
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed({
                'error': {
                    'code': 'token_expired',
                    'message': 'Token has expired',
                    'details': {
                        'expired_at': datetime.fromtimestamp(
                            jwt.decode(token, options={"verify_signature": False})['exp']
                        ).isoformat()
                    }
                }
            })
        except jwt.InvalidTokenError as e:
            raise AuthenticationFailed({
                'error': {
                    'code': 'invalid_token',
                    'message': str(e),
                    'retryable': True
                }
            })
