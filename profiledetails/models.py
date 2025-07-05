from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField

class ProfileDetails(models.Model):
    LEARNING_STYLES = [
        ('visual', 'Visual'),
        ('auditory', 'Auditory'),
        ('reading_writing', 'Reading/Writing'),
        ('kinesthetic', 'Kinesthetic'),
    ]
    
    STUDENT_TYPES = [
        ('beginner', 'Beginner'),
        ('student', 'Student'),
        ('professional', 'Professional'),
        ('career_changer', 'Career Changer'),
        ('hobbyist', 'Hobbyist'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile_details'
    )
    
    # Personal Information
    about = models.TextField(blank=True, null=True, help_text="A brief description about the user")
    background = models.TextField(blank=True, null=True, help_text="Educational and professional background")
    
    # Educational Details
    student_type = models.CharField(
        max_length=20,
        choices=STUDENT_TYPES,
        blank=True,
        null=True,
        help_text="Type of student"
    )
    
    # Learning Preferences
    preferred_learning_style = models.CharField(
        max_length=20,
        choices=LEARNING_STYLES,
        blank=True,
        null=True,
        help_text="Preferred learning style from VARK model"
    )
    learning_preference = models.TextField(blank=True, null=True, help_text="Additional learning preferences or notes")
    
    # New fields
    strengths = ArrayField(
        models.CharField(max_length=100),
        blank=True,
        default=list,
        help_text="List of user's strengths"
    )
    weaknesses = ArrayField(
        models.CharField(max_length=100),
        blank=True,
        default=list,
        help_text="Areas for improvement"
    )
    skill_levels = JSONField(
        default=dict,
        blank=True,
        help_text="Stores skill assessments in format {category: level}"
    )
    learning_goals = JSONField(
        default=list,
        blank=True,
        help_text="Stores learning goals as an array of objects"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Profile Details'
        ordering = ['-created_at']

    def __str__(self):
        return f"Profile - {self.user.email}"