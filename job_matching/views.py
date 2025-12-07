from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Q
import requests
import json
from datetime import timedelta
from django.utils import timezone
import uuid
import logging

from .models import (
    StudentProfile, JobListing, JobMatchResult, JobSearchQuery, Skill
)
from .serializers import (
    StudentProfileSerializer, JobListingSerializer, JobMatchResultSerializer,
    JobSearchQuerySerializer, SkillExtractionRequestSerializer,
    JobSearchRequestSerializer, JobMatchRequestSerializer,
    GeneratePrepPlanRequestSerializer, SchedulePrepPlanRequestSerializer
)

User = get_user_model()
logger = logging.getLogger(__name__)

class IsStudentUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'student_profile')

class ExtractSkillsView(APIView):
    permission_classes = [IsAuthenticated, IsStudentUser]
    
    def post(self, request):
        serializer = SkillExtractionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        student_profile, created = StudentProfile.objects.get_or_create(user=request.user)
        skills = self.extract_skills_from_sources(serializer.validated_data)
        
        if skills:
            student_profile.skills = skills
            student_profile.save()
            return Response({"status": "success", "skills": skills})
        return Response(
            {"error": "Could not extract skills from the provided sources"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def extract_skills_from_sources(self, data):
        # TODO: Implement actual skill extraction from GitHub and Notion
        # This is a placeholder implementation
        return {
            "Python": 0.85,
            "Django": 0.75,
            "Cybersecurity": 0.65,
            "Penetration Testing": 0.60
        }

class SearchJobsView(APIView):
    permission_classes = [IsAuthenticated, IsStudentUser]
    
    def post(self, request):
        serializer = JobSearchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        search_params = serializer.validated_data
        jobs = self.search_job_api(search_params)
        
        # Log the search query
        JobSearchQuery.objects.create(
            student=request.user,
            query_params=search_params,
            total_results=len(jobs) if jobs else 0
        )
        
        return Response({"jobs": jobs})
    
    def search_job_api(self, params):
        # TODO: Implement actual JSearch API integration
        # This is a mock implementation
        return [
            {
                "id": str(uuid.uuid4()),
                "title": "Cybersecurity Intern",
                "company": "SecureCorp",
                "description": "Cybersecurity internship focusing on penetration testing.",
                "requirements": ["Python", "Cybersecurity", "Networking"],
                "location": "Remote",
                "job_type": "internship",
                "apply_link": "https://example.com/apply/1",
                "posted_date": "2023-11-01"
            }
        ]

class MatchJobsView(APIView):
    permission_classes = [IsAuthenticated, IsStudentUser]
    
    def post(self, request):
        serializer = JobMatchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        job_id = serializer.validated_data['job_id']
        student_id = serializer.validated_data.get('student_id', request.user.id)
        
        try:
            job = JobListing.objects.get(id=job_id)
            student = User.objects.get(id=student_id)
            student_profile = student.student_profile
            
            # Calculate match score
            match_result = self.calculate_job_match(student_profile, job)
            
            # Save or update match result
            match, created = JobMatchResult.objects.update_or_create(
                student=student,
                job=job,
                defaults={
                    'match_score': match_result['match_score'],
                    'missing_skills': match_result['missing_skills'],
                    'readiness_days': match_result['readiness_days']
                }
            )
            
            return Response(JobMatchResultSerializer(match).data)
            
        except (JobListing.DoesNotExist, User.DoesNotExist) as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def calculate_job_match(self, student_profile, job):
        # TODO: Implement more sophisticated matching algorithm
        # This is a simplified implementation
        student_skills = set(skill.lower() for skill in student_profile.skills.keys())
        job_requirements = set(req.lower() for req in job.requirements)
        
        if not job_requirements:
            return {
                'match_score': 0,
                'missing_skills': [],
                'readiness_days': 0
            }
            
        common_skills = student_skills.intersection(job_requirements)
        missing_skills = job_requirements - student_skills
        match_percentage = (len(common_skills) / len(job_requirements)) * 100
        
        # Simple readiness days calculation
        readiness_days = len(missing_skills) * 3  # 3 days per missing skill as a placeholder
        
        return {
            'match_score': round(match_percentage, 2),
            'missing_skills': list(missing_skills),
            'readiness_days': min(readiness_days, 90)  # Cap at 90 days
        }

class UserSkillsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get or create student profile
        student_profile, created = StudentProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'skills': {},
                'training_track': '',
                'weak_points': []
            }
        )
        
        return Response({
            "skills": student_profile.skills or {},
            "training_track": student_profile.training_track or "",
            "weak_points": student_profile.weak_points or []
        })

class GeneratePrepPlanView(APIView):
    permission_classes = [IsAuthenticated, IsStudentUser]
    
    def post(self, request):
        serializer = GeneratePrepPlanRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        job_id = serializer.validated_data['job_id']
        student_id = serializer.validated_data.get('student_id', request.user.id)
        days_available = serializer.validated_data['days_available']
        
        try:
            job_match = JobMatchResult.objects.get(
                job_id=job_id,
                student_id=student_id
            )
            
            prep_plan = self.generate_prep_plan(job_match, days_available)
            job_match.prep_plan = prep_plan
            job_match.save()
            
            return Response({
                "status": "success",
                "prep_plan": prep_plan,
                "job_match_id": str(job_match.id)
            })
            
        except JobMatchResult.DoesNotExist:
            return Response(
                {"error": "Job match not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def generate_prep_plan(self, job_match, days_available):
        # TODO: Implement AI-powered prep plan generation
        # This is a mock implementation
        missing_skills = job_match.missing_skills or []
        days_per_skill = max(1, days_available // max(1, len(missing_skills)))
        
        plan = {
            "days_available": days_available,
            "skills_to_learn": missing_skills,
            "daily_study_hours": 2,
            "schedule": []
        }
        
        current_date = timezone.now().date()
        
        for i, skill in enumerate(missing_skills, 1):
            for day in range(days_per_skill):
                plan["schedule"].append({
                    "date": (current_date + timedelta(days=day)).isoformat(),
                    "skill": skill,
                    "topics": [f"{skill} Fundamentals", f"{skill} Practice"],
                    "resources": [
                        f"https://example.com/learn/{skill.lower().replace(' ', '-')}",
                        f"https://youtube.com/search?q={skill}+tutorial"
                    ]
                })
            current_date += timedelta(days=days_per_skill)
        
        return plan

class SchedulePrepPlanView(APIView):
    permission_classes = [IsAuthenticated, IsStudentUser]
    
    def post(self, request):
        serializer = SchedulePrepPlanRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        prep_plan_id = serializer.validated_data['prep_plan_id']
        start_date = serializer.validated_data['start_date']
        daily_study_hours = serializer.validated_data['daily_study_hours']
        
        try:
            job_match = JobMatchResult.objects.get(
                id=prep_plan_id,
                student=request.user
            )
            
            if not job_match.prep_plan:
                return Response(
                    {"error": "No preparation plan found for this job match"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # TODO: Implement actual Google Calendar integration
            # This is a mock implementation
            events = self.schedule_calendar_events(
                job_match, start_date, daily_study_hours
            )
            
            job_match.calendar_events = events
            job_match.save()
            
            return Response({
                "status": "success",
                "scheduled_events": events
            })
            
        except JobMatchResult.DoesNotExist:
            return Response(
                {"error": "Job match not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def schedule_calendar_events(self, job_match, start_date, daily_study_hours):
        # TODO: Implement actual Google Calendar integration
        # This is a mock implementation
        events = []
        current_date = start_date
        prep_plan = job_match.prep_plan.get('schedule', [])
        
        for i, day_plan in enumerate(prep_plan, 1):
            event = {
                "id": f"event_{i}_{job_match.id}",
                "summary": f"Study: {day_plan.get('skill', 'New Skill')}",
                "description": f"Topics: {', '.join(day_plan.get('topics', []))}",
                "start": {
                    "dateTime": f"{current_date}T09:00:00",
                    "timeZone": "UTC"
                },
                "end": {
                    "dateTime": f"{current_date}T{9 + daily_study_hours}:00:00",
                    "timeZone": "UTC"
                }
            }
            events.append(event)
            current_date += timedelta(days=1)
        
        return events

class JobRecommendationsView(generics.ListAPIView):
    serializer_class = JobMatchResultSerializer
    permission_classes = [IsAuthenticated, IsStudentUser]
    
    def get_queryset(self):
        # Get the top 10 job matches for the current user
        return JobMatchResult.objects.filter(
            student=self.request.user,
            match_score__gte=75  # Only show matches with 75% or higher
        ).select_related('job').order_by('-match_score')[:10]

class StudentProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated, IsStudentUser]
    
    def get_object(self):
        profile, created = StudentProfile.objects.get_or_create(user=self.request.user)
        return profile

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)