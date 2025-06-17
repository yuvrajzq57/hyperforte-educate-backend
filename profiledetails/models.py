from django.db import models
from django.conf import settings

class ProfileDetails(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile_details'
    )
    about = models.TextField(max_length=500, blank=True)
    background = models.TextField(max_length=1000, blank=True)
    student_type = models.CharField(max_length=50, blank=True)
    preferred_learning_style = models.CharField(max_length=50, blank=True)
    learning_preference = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Profile Details'

    def __str__(self):
        return f"{self.user.username}'s profile"