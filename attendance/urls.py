from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    QRCodeScanView,
    MarkAttendanceView,
    HealthCheckView
)

app_name = 'attendance'

# Create a router and register our viewsets with it
router = DefaultRouter()

# API v1 URL patterns
api_v1 = [
    # QR Code scanning endpoint (for students)
    path('scan/', QRCodeScanView.as_view(), name='qr-scan'),
    
    # Mark attendance after validation (for Educate Portal)
    path('mark-attendance/', MarkAttendanceView.as_view(), name='mark-attendance'),
    
    # Health check endpoint
    path('health/', HealthCheckView.as_view(), name='health-check'),
]

# Root URL patterns
urlpatterns = [
    # API v1
    path('api/v1/attendance/', include((api_v1, 'attendance'))),
]

# Include the router URLs
urlpatterns += router.urls
