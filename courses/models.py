from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

def course_thumbnail_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/courses/<id>/<filename>
    return f'courses/{instance.id}/{filename}'

class Course(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    learning_outcomes = models.TextField(blank=True)
    prerequisites = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to=course_thumbnail_path, null=True, blank=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    language = models.CharField(max_length=50, default='English')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_free = models.BooleanField(default=False)
    estimated_duration = models.PositiveIntegerField(help_text="Duration in minutes")
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='courses_taught')
    students = models.ManyToManyField(User, related_name='courses_enrolled', blank=True)
    average_rating = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    total_reviews = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

def module_image_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/courses/<course_id>/modules/<module_id>/<filename>
    return f'courses/{instance.course.id}/modules/{instance.id}/{filename}'

class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    objectives = models.TextField(blank=True)
    order_number = models.PositiveIntegerField()
    image = models.URLField(max_length=500, blank=True, null=True)
    is_free = models.BooleanField(default=False)
    estimated_duration = models.PositiveIntegerField(help_text="Duration in minutes", default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order_number']
        unique_together = ['course', 'order_number']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

def section_media_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/courses/<course_id>/modules/<module_id>/sections/<section_id>/<filename>
    return f'courses/{instance.module.course.id}/modules/{instance.module.id}/sections/{instance.id}/{filename}'

class Section(models.Model):
    CONTENT_TYPES = [
        ('text', 'Text'),
        ('video', 'Video'),
        ('quiz', 'Quiz'),
        ('file', 'File'),
        ('link', 'External Link'),
        ('assignment', 'Assignment'),
    ]
    
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    content_type = models.CharField(max_length=15, choices=CONTENT_TYPES)
    video_url = models.URLField(blank=True, null=True)
    attachment = models.FileField(upload_to=section_media_path, null=True, blank=True)
    external_url = models.URLField(blank=True, null=True)
    order_number = models.PositiveIntegerField()
    summary = models.TextField(blank=True)
    is_free = models.BooleanField(default=False)
    estimated_duration = models.PositiveIntegerField(help_text="Duration in minutes", default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['order_number']
        unique_together = ['module', 'order_number']

    def __str__(self):
        return f"{self.module.title} - {self.title}"

class Quiz(models.Model):
    module = models.OneToOneField(Module, on_delete=models.CASCADE, related_name='quiz')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    passing_score = models.PositiveIntegerField(
        default=70,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Passing percentage score (1-100)"
    )
    time_limit = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Time limit in minutes (optional)"
    )
    max_attempts = models.PositiveIntegerField(
        default=1,
        help_text="Maximum number of attempts allowed (0 for unlimited)"
    )
    show_correct_answers = models.BooleanField(
        default=True,
        help_text="Whether to show correct answers after submission"
    )
    require_passing = models.BooleanField(
        default=True,
        help_text="Whether passing this quiz is required to complete the module"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Quiz for {self.module.title}"

class Question(models.Model):
    QUESTION_TYPES = [
        ('single_choice', 'Single Choice'),
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('essay', 'Essay'),
    ]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='single_choice')
    explanation = models.TextField(blank=True, help_text="Explanation of the correct answer")
    points = models.PositiveIntegerField(default=1, help_text="Points awarded for correct answer")
    order_number = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order_number']

    def __str__(self):
        return f"Q{self.order_number}: {self.question_text[:50]}..."

class QuestionOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_text = models.TextField()
    is_correct = models.BooleanField(default=False)
    feedback = models.TextField(blank=True, help_text="Feedback to show when this option is selected")
    order_number = models.PositiveIntegerField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

class UserQuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='user_attempts')
    score = models.FloatField()
    passed = models.BooleanField()
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(auto_now_add=True)
    time_spent = models.PositiveIntegerField(help_text="Time spent in seconds")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-completed_at']
        get_latest_by = 'completed_at'
    
    def __str__(self):
        return f"{self.user.username}'s attempt at {self.quiz.title}"

class UserQuizResponse(models.Model):
    attempt = models.ForeignKey(UserQuizAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_options = models.ManyToManyField(QuestionOption, blank=True)
    text_response = models.TextField(blank=True)
    is_correct = models.BooleanField()
    points_earned = models.FloatField()
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['question__order_number']
    
    def __str__(self):
        return f"Response to {self.question.id} in attempt {self.attempt.id}"
        return f"{self.option_text[:30]}..."
