from rest_framework.throttling import UserRateThrottle
from django.conf import settings

class AttendanceRateThrottle(UserRateThrottle):
    """
    Custom throttle for attendance marking endpoint.
    Rate limit is configurable via ATTENDANCE_RATE_LIMIT setting.
    Defaults to '5/minute' if not set.
    """
    scope = 'attendance'
    
    def __init__(self):
        super().__init__()
        self.rate = getattr(settings, 'ATTENDANCE_RATE_LIMIT', '5/minute')
    
    def parse_rate(self, rate):
        """
        Override to handle the rate string format.
        Expected format: '5/minute' or '10/hour'
        """
        if rate is None:
            return (None, None)
            
        try:
            num_requests, period = rate.split('/')
            num_requests = int(num_requests)
            
            # Convert period to seconds
            if period.startswith('second'):
                period_seconds = 1
            elif period.startswith('minute'):
                period_seconds = 60
            elif period.startswith('hour'):
                period_seconds = 3600
            elif period.startswith('day'):
                period_seconds = 86400
            else:
                raise ValueError("Period must be 'second', 'minute', 'hour', or 'day'")
                
            return (num_requests, period_seconds)
            
        except (ValueError, AttributeError) as e:
            # Fall back to default if rate is invalid
            return (5, 60)  # 5 per minute default
