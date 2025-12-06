from django.db import models
from django.conf import settings
from django.utils import timezone

class MCPUserIntegration(models.Model):
    """Tracks MCP integration status for each user."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mcp_integration'
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether MCP integration is enabled for this user"
    )
    last_synced = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the user's GitHub data was last synced with MCP"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "MCP User Integration"
        verbose_name_plural = "MCP User Integrations"

    def __str__(self):
        return f"MCP Integration - {self.user.email}"

    def update_last_synced(self):
        """Update the last_synced timestamp."""
        self.last_synced = timezone.now()
        self.save(update_fields=['last_synced', 'updated_at'])

    @property
    def is_connected(self) -> bool:
        """Check if the user has an active MCP integration."""
        return self.is_active and hasattr(self.user, 'githubuser') and self.user.githubuser.access_token is not None
