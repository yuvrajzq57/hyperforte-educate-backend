from django.urls import path
from . import views

app_name = 'studyplan'

urlpatterns = [
    # User study plan endpoints
    path('', views.UserStudyPlanView.as_view(), name='user-study-plan'),
    
    # Study plan status endpoint
    path('status/', views.StudyPlanStatusView.as_view(), name='study-plan-status'),
]
