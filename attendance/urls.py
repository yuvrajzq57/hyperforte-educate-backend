from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    QRCodeScanView,
    MarkAttendanceView,
    HealthCheckView
)

app_name = 'attendance'

# Create a router and register our viewsets with it
router = DefaultRouter()

urlpatterns = [
    # QR Code scanning endpoint (for students)
    path('scan/', QRCodeScanView.as_view(), name='qr-scan'),
    
    # Mark attendance after validation (for Educate Portal)
    path('mark/', MarkAttendanceView.as_view(), name='mark-attendance'),
    
    # Health check endpoint
    path('health/', HealthCheckView.as_view(), name='health-check'),
]

# Include the router URLs
urlpatterns += router.urls
