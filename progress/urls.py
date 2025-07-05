from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'progress'

urlpatterns = [
    # Get progress for all modules in a course
    path('courses/<int:course_id>/modules/', 
         views.ModuleProgressListView.as_view(), 
         name='module-progress-list'),
    
    # Get or update section progress
    path('sections/<int:section_id>/progress/', 
         views.SectionProgressView.as_view(), 
         name='section-progress'),
    
    # List or create quiz attempts
    path('quizzes/<int:quiz_id>/attempts/', 
         views.QuizAttemptView.as_view(), 
         name='quiz-attempts'),
    
    # Get user's progress overview
    path('overview/', 
         views.UserProgressOverview.as_view(), 
         name='user-progress-overview'),
]
