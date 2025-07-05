from django.db import models
from django.conf import settings
from django.utils import timezone

class UserStudyPlan(models.Model):
    """Model to store user's study plan preferences."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='study_plan'
    )
    enabled = models.BooleanField(
        default=True,
        help_text="Whether the study plan is active"
    )
    preferred_time = models.TimeField(
        null=True, 
        blank=True,
        help_text="Preferred time of day for study sessions"
    )
    reminder_email = models.BooleanField(
        default=True,
        help_text="Whether to send email reminders"
    )
    target_completion_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Target date to complete the study plan"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Study Plan'
        verbose_name_plural = 'User Study Plans'

    def __str__(self):
        return f"Study Plan - {self.user.email}"

    def get_study_days_display(self):
        """Return a list of day names for the study days."""
        return [day.get_day_of_week_display() for day in self.study_days.all()]


class StudyPlanDay(models.Model):
    """Model to store which days of the week a user wants to study."""
    DAY_CHOICES = [
        (0, 'Sunday'),
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
    ]
    
    study_plan = models.ForeignKey(
        UserStudyPlan, 
        on_delete=models.CASCADE, 
        related_name='study_days'
    )
    day_of_week = models.PositiveSmallIntegerField(
        choices=DAY_CHOICES,
        help_text="Day of the week (0=Sunday, 1=Monday, etc.)"
    )

    class Meta:
        verbose_name = 'Study Plan Day'
        verbose_name_plural = 'Study Plan Days'
        unique_together = ['study_plan', 'day_of_week']
        ordering = ['day_of_week']

    def __str__(self):
        return f"{self.study_plan.user.email} - {self.get_day_of_week_display()}"
