import json
import logging
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

def get_required_setting(name):
    """Helper to get required settings with proper error message."""
    value = getattr(settings, name, None)
    if not value:
        raise ImproperlyConfigured(f"Required setting {name} is missing")
    return value

class SPOCClientError(Exception):
    """Base exception for SPOC client errors."""
    pass

def create_session():
    """Create a requests session with retry logic."""
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
    )
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

def verify_token(session_id, token):
    """
    Verify a session token with the SPOC service.
    
    Args:
        session_id: UUID of the session
        token: JWT token from the QR code
        
    Returns:
        dict: Response from the SPOC service
        
    Raises:
        SPOCClientError: If verification fails or response is invalid
    """
    base_url = get_required_setting('SPOC_BASE_URL')
    timeout = getattr(settings, 'SPOC_VERIFY_TIMEOUT_SECONDS', 5)
    
    # Get QR code for the session
    url = urljoin(base_url, f'/api/attendance/verify/')  # Updated endpoint
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'  # Add Authorization header
    }
    
    try:
        session = create_session()
        response = session.post(
            url,
            headers=headers,
            json={
                'session_id': str(session_id),
                'token': token
            },
            timeout=timeout
        )
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to verify token: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                error_msg = error_data.get('detail', error_msg)
            except:
                error_msg = e.response.text or error_msg
        logger.error(error_msg)
        raise SPOCClientError(error_msg)

def push_mark(session_id, student_id):
    """
    Notify SPOC service about a student's attendance.
    
    Args:
        session_id: UUID of the session
        student_id: ID of the student
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not getattr(settings, 'SPOC_MARK_ENABLED', True):
        return False
        
    base_url = get_required_setting('SPOC_BASE_URL')
    api_key = get_required_setting('SPOC_API_KEY')
    timeout = getattr(settings, 'SPOC_MARK_TIMEOUT_SECONDS', 3)
    
    url = urljoin(base_url, '/api/attendance/mark-attendance/')
    headers = {
        'X-API-Key': api_key,
        'Content-Type': 'application/json',
    }
    
    data = {
        'session_id': str(session_id),
        'student_id': str(student_id),
        'timestamp': timezone.now().isoformat(),
    }
    
    try:
        session = create_session()
        response = session.post(
            url,
            headers=headers,
            json=data,
            timeout=timeout
        )
        
        # We don't raise for status here since this is fire-and-forget
        if response.status_code == 200:
            return True
            
        logger.warning(
            f'SPOC mark request failed with status {response.status_code}: {response.text}'
        )
        return False
        
    except Exception as e:
        logger.error(f'SPOC mark request failed: {str(e)}')
        return False
