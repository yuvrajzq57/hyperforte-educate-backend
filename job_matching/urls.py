from django.urls import path
from . import views

app_name = 'job_matching'

urlpatterns = [
    # Profile Management
    path('profile/', views.StudentProfileView.as_view(), name='student-profile'),
    path('profile/skills/', views.UserSkillsView.as_view(), name='user-skills'),
    
    # Skill Extraction
    path('skills/extract/', views.ExtractSkillsView.as_view(), name='extract-skills'),
    
    # Job Search and Matching
    path('jobs/search/', views.SearchJobsView.as_view(), name='search-jobs'),
    path('jobs/match/', views.MatchJobsView.as_view(), name='match-jobs'),
    path('jobs/recommendations/', views.JobRecommendationsView.as_view(), 
         name='job-recommendations'),
    
    # Preparation Plan
    path('jobs/generate-prep-plan/', views.GeneratePrepPlanView.as_view(), 
         name='generate-prep-plan'),
    path('jobs/schedule-prep-plan/', views.SchedulePrepPlanView.as_view(), 
         name='schedule-prep-plan'),
]