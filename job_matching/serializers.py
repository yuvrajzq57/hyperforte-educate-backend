from rest_framework import serializers
from .models import (
    StudentProfile, JobListing, JobMatchResult, JobSearchQuery, Skill
)
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name')

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'

class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    skills = serializers.JSONField(required=False)
    weak_points = serializers.JSONField(required=False)

    class Meta:
        model = StudentProfile
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class JobListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobListing
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class JobMatchResultSerializer(serializers.ModelSerializer):
    job = JobListingSerializer(read_only=True)
    student = UserSerializer(read_only=True)
    missing_skills = serializers.JSONField(required=False)
    prep_plan = serializers.JSONField(required=False)
    calendar_events = serializers.JSONField(required=False)

    class Meta:
        model = JobMatchResult
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class JobSearchQuerySerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    query_params = serializers.JSONField()

    class Meta:
        model = JobSearchQuery
        fields = '__all__'
        read_only_fields = ('created_at',)

class SkillExtractionRequestSerializer(serializers.Serializer):
    github_username = serializers.CharField(required=False)
    notion_integration_id = serializers.CharField(required=False)

class JobSearchRequestSerializer(serializers.Serializer):
    search_terms = serializers.CharField(required=False)
    location = serializers.CharField(required=False)
    job_type = serializers.ChoiceField(
        choices=JobListing.JOB_TYPES,
        required=False
    )
    min_salary = serializers.IntegerField(required=False, min_value=0)
    experience_level = serializers.ChoiceField(
        choices=[
            ('internship', 'Internship'),
            ('entry_level', 'Entry Level'),
            ('mid_level', 'Mid Level'),
            ('senior', 'Senior'),
            ('lead', 'Lead'),
            ('manager', 'Manager'),
            ('executive', 'Executive')
        ],
        required=False
    )

class JobMatchRequestSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    student_id = serializers.IntegerField(required=False)

class GeneratePrepPlanRequestSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    student_id = serializers.IntegerField(required=False)
    days_available = serializers.IntegerField(min_value=7, max_value=90, default=21)

class SchedulePrepPlanRequestSerializer(serializers.Serializer):
    prep_plan_id = serializers.UUIDField()
    calendar_id = serializers.CharField(required=False)
    start_date = serializers.DateField()
    daily_study_hours = serializers.IntegerField(min_value=1, max_value=8, default=2)
