from django.db import models
from django.conf import settings

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
