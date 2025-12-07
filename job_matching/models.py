from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()

class StudentProfile(models.Model):
    """Stores student's professional profile and skills."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='job_profile')
    skills = models.JSONField(default=dict, help_text="Dictionary of skills with confidence scores")
    training_track = models.CharField(max_length=100, blank=True, null=True)
    weak_points = models.JSONField(default=list, help_text="List of areas needing improvement")
    github_username = models.CharField(max_length=100, blank=True, null=True)
    notion_integration_id = models.CharField(max_length=100, blank=True, null=True)
    calendar_integration_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email}'s Job Profile"

    class Meta:
        verbose_name = "Student Profile"
        verbose_name_plural = "Student Profiles"


class JobListing(models.Model):
    """Stores job/internship listings from external APIs."""
    JOB_TYPES = [
        ('internship', 'Internship'),
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.JSONField(help_text="List of required skills and qualifications")
    location = models.CharField(max_length=255)
    job_type = models.CharField(max_length=50, choices=JOB_TYPES)
    apply_link = models.URLField(max_length=500)
    posted_date = models.DateField()
    is_active = models.BooleanField(default=True)
    source = models.CharField(max_length=100, default="JSearch")
    raw_data = models.JSONField(default=dict, help_text="Raw data from the job API")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} at {self.company}"

    class Meta:
        ordering = ['-posted_date']
        indexes = [
            models.Index(fields=['title', 'company']),
            models.Index(fields=['job_type', 'is_active']),
        ]


class JobMatchResult(models.Model):
    """Stores matching results between students and job listings."""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_matches')
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name='student_matches')
    match_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Matching percentage (0-100)"
    )
    missing_skills = models.JSONField(default=list, help_text="List of skills the student is missing")
    readiness_days = models.PositiveIntegerField(help_text="Estimated days until job-ready")
    prep_plan = models.JSONField(default=dict, help_text="Generated preparation plan")
    is_interested = models.BooleanField(default=False)
    application_status = models.CharField(
        max_length=50,
        choices=[
            ('not_applied', 'Not Applied'),
            ('applied', 'Applied'),
            ('interviewing', 'Interviewing'),
            ('rejected', 'Rejected'),
            ('accepted', 'Accepted')
        ],
        default='not_applied'
    )
    calendar_events = models.JSONField(default=list, help_text="List of calendar event IDs for prep plan")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'job')
        ordering = ['-match_score', '-created_at']
        verbose_name = "Job Match"
        verbose_name_plural = "Job Matches"

    def __str__(self):
        return f"{self.student.email} - {self.job.title} ({self.match_score}%)"


class JobSearchQuery(models.Model):
    """Stores job search queries and results."""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_searches')
    query_params = models.JSONField(help_text="Parameters used for the job search")
    total_results = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.email} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class Skill(models.Model):
    """Master list of skills with categories and metadata."""
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    difficulty_level = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Relative difficulty to learn (1-5)"
    )
    average_learning_hours = models.PositiveIntegerField(
        default=20,
        help_text="Average hours needed to learn this skill"
    )
    related_skills = models.ManyToManyField('self', blank=True, symmetrical=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
        ]
