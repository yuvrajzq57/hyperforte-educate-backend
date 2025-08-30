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
urlpatterns = [
    # QR Code scanning endpoint (for students)
    path('api/v1/attendance/scan/', QRCodeScanView.as_view(), name='qr-scan'),
    
    # Mark attendance after validation (for Educate Portal)
    path('api/v1/attendance/mark-attendance/', MarkAttendanceView.as_view(), name='mark-attendance'),
    
    # Health check endpoint
    path('api/v1/attendance/health/', HealthCheckView.as_view(), name='health-check'),
]
