from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class Course(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    thumbnail_url = models.URLField(blank=True, null=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    estimated_duration = models.PositiveIntegerField(help_text="Duration in minutes")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order_number = models.PositiveIntegerField()
    image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order_number']
        unique_together = ['course', 'order_number']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Section(models.Model):
    CONTENT_TYPES = [
        ('text', 'Text'),
        ('video', 'Video'),
        ('quiz', 'Quiz'),
    ]
    
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES)
    video_url = models.URLField(blank=True, null=True)
    order_number = models.PositiveIntegerField()
    summary = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order_number']
        unique_together = ['module', 'order_number']

    def __str__(self):
        return f"{self.module.title} - {self.title}"

class Quiz(models.Model):
    module = models.OneToOneField(Module, on_delete=models.CASCADE, related_name='quiz')
    title = models.CharField(max_length=255)
    passing_score = models.PositiveIntegerField(default=70)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Quiz for {self.module.title}"

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    order_number = models.PositiveIntegerField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['order_number']

    def __str__(self):
        return f"Q{self.order_number}: {self.question_text[:50]}..."

class QuestionOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_text = models.TextField()
    is_correct = models.BooleanField(default=False)
    order_number = models.PositiveIntegerField()

    class Meta:
        ordering = ['order_number']

    def __str__(self):
        return f"{self.option_text[:30]}..."
