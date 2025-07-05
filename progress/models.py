from django.db import models
from django.conf import settings
from django.utils import timezone
from courses.models import Module, Section, Quiz

class UserModuleProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='module_progress')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='user_progress')
    is_completed = models.BooleanField(default=False)
    progress_percentage = models.FloatField(default=0.0)
    last_accessed = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'User Module Progress'
        unique_together = ['user', 'module']
        ordering = ['-last_accessed']

    def __str__(self):
        return f"{self.user.email} - {self.module.title} ({self.progress_percentage}%)"

    def update_progress(self):
        """Update the progress percentage based on completed sections"""
        total_sections = self.module.sections.count()
        if total_sections == 0:
            self.progress_percentage = 100.0
        else:
            completed_sections = UserSectionProgress.objects.filter(
                user=self.user,
                section__module=self.module,
                is_completed=True
            ).count()
            self.progress_percentage = (completed_sections / total_sections) * 100
        
        # Update completion status
        if self.progress_percentage >= 100 and not self.is_completed:
            self.is_completed = True
            self.completed_at = timezone.now()
        elif self.progress_percentage < 100 and self.is_completed:
            self.is_completed = False
            self.completed_at = None
            
        self.save()

class UserSectionProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='section_progress')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='user_progress')
    is_completed = models.BooleanField(default=False)
    last_accessed = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_position = models.FloatField(default=0.0, help_text="Last position in video/audio in seconds")

    class Meta:
        verbose_name_plural = 'User Section Progress'
        unique_together = ['user', 'section']
        ordering = ['-last_accessed']

    def __str__(self):
        return f"{self.user.email} - {self.section.title} ({'Completed' if self.is_completed else 'In Progress'})"

    def save(self, *args, **kwargs):
        # Update completed_at timestamp when section is marked as completed
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        elif not self.is_completed and self.completed_at:
            self.completed_at = None
        super().save(*args, **kwargs)
        
        # Update module progress
        module_progress, created = UserModuleProgress.objects.get_or_create(
            user=self.user,
            module=self.section.module
        )
        module_progress.update_progress()

class UserQuizAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.FloatField(null=True, blank=True, help_text="Score in percentage")
    passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_taken = models.PositiveIntegerField(help_text="Time taken in seconds", default=0)

    class Meta:
        ordering = ['-completed_at']
        verbose_name_plural = 'User Quiz Attempts'

    def __str__(self):
        return f"{self.user.email} - {self.quiz.title} - {self.score}%"

    def save(self, *args, **kwargs):
        # If this is a new attempt and has a score, mark as completed
        if self.score is not None and not self.completed_at:
            self.completed_at = timezone.now()
            self.passed = self.score >= self.quiz.passing_score
        super().save(*args, **kwargs)
