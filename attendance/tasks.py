import json
import logging
import requests
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from requests.exceptions import RequestException
from .models import AttendanceRecord

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def push_mark_to_spoc(self, session_id, student_external_id, token, method='QR'):
    """
    Background task to forward attendance data to the SPOC server.
    
    Args:
        session_id (str): The session ID for the attendance
        student_external_id (str): External ID of the student
        token (str): Authentication token for the SPOC server
        method (str): Method of attendance marking (default: 'QR')
    """
    # Get SPOC base URL from settings (prefer SPOC_BASE_URL per contract)
    spoc_base = getattr(settings, 'SPOC_BASE_URL', None) or getattr(settings, 'SPOC_SERVER_URL', '')
    endpoint = f"{spoc_base.rstrip('/')}/api/attendance/mark"
    
    # Prepare the payload
    payload = {
        "session_id": str(session_id),
        "student_external_id": student_external_id,
        "status": "present",
        "method": method,
        "source": "EDUCATE"
    }
    
    # Add headers
    headers = {
        'Content-Type': 'application/json',
        # Per SPOC contract: pass QR JWT in Authorization header as Bearer
        'Authorization': f'Bearer {token}'
    }
    
    # Create a unique key for this attendance record to prevent duplicates
    cache_key = f'attendance_{session_id}_{student_external_id}'
    
    try:
        # Check if this attendance has already been processed
        if cache.get(cache_key):
            logger.info(f"Attendance already processed for session {session_id} and student {student_external_id}")
            return {"status": "already_processed", "message": "Attendance already processed"}
        
        logger.info(f"Forwarding attendance to SPOC server: {endpoint}")
        
        # Make the POST request to SPOC server
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=10  # 10 seconds timeout
        )
        
        # Attempt to parse response JSON for logging
        resp_json = None
        try:
            resp_json = response.json()
        except Exception:
            resp_json = None

        # Check for successful response
        if response.status_code >= 400:
            # Log error details from SPOC
            logger.error(
                "SPOC mark failed: %s %s | body=%s",
                response.status_code,
                response.text[:500],
                json.dumps(resp_json) if resp_json is not None else 'N/A'
            )
            response.raise_for_status()
        
        # Mark as processed in cache (expires in 24 hours)
        cache.set(cache_key, True, timeout=60 * 60 * 24)
        
        logger.info(f"Successfully forwarded attendance to SPOC server: {response.text}")

        # Mark the corresponding attendance record as synced if we can locate it
        try:
            rec = AttendanceRecord.objects.filter(
                external_session_id=session_id,
                student_external_id=student_external_id
            ).order_by('-marked_at').first()
            if rec:
                rec.mark_synced(True)
        except Exception as e:
            logger.warning(f"Could not mark AttendanceRecord as synced: {e}")

        return {"status": "success", "data": resp_json or {}}
        
    except RequestException as e:
        error_msg = f"Failed to forward attendance to SPOC server: {str(e)}"
        logger.error(error_msg)

        # Try to mark record as not synced with error
        try:
            rec = AttendanceRecord.objects.filter(
                external_session_id=session_id,
                student_external_id=student_external_id
            ).order_by('-marked_at').first()
            if rec:
                rec.mark_synced(False, error_msg)
        except Exception as mark_err:
            logger.warning(f"Could not update AttendanceRecord sync status: {mark_err}")
        
        # Retry on failure (Celery will handle the retry logic)
        if self.request.retries < self.max_retries:
            retry_in = self.default_retry_delay * (2 ** self.request.retries)
            logger.warning(f"Retrying in {retry_in} seconds... (Attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e, countdown=retry_in)
        
        return {"status": "error", "message": error_msg}
