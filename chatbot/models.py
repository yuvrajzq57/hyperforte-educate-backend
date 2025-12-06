from django.db import models
from django.conf import settings
from django.utils import timezone

class ChatMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    module_id = models.IntegerField()
    message = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - Module {self.module_id} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class ChatContext(models.Model):
    """Optional model to store context per user/module"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    module_id = models.IntegerField()
    context = models.JSONField(default=dict)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'module_id']

    def __str__(self):
        return f"Context for {self.user.username} - Module {self.module_id}"


class GitHubUser(models.Model):
    """Model to store GitHub OAuth tokens for users"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    github_username = models.CharField(max_length=100, blank=True, null=True)
    access_token = models.CharField(max_length=255, blank=True, null=True)
    token_expires = models.DateTimeField(blank=True, null=True)
    refresh_token = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_token_expired(self):
        if not self.token_expires:
            return True
        return timezone.now() >= self.token_expires

    def __str__(self):
        return f"{self.user.username}'s GitHub Account"
