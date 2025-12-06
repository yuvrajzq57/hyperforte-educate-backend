from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import logging
from importlib import import_module

logger = logging.getLogger(__name__)

# Try to import the GitHubUser model from the correct app
try:
    from chatbot.models import GitHubUser
except (ImportError, AttributeError) as e:
    logger.warning(f"Could not import GitHubUser model from chatbot.models: {str(e)}. Signals will not work.")
    GitHubUser = None

if GitHubUser:
    @receiver(post_save, sender=GitHubUser)
    def setup_mcp_integration(sender, instance, created, **kwargs):
        """
        Automatically set up MCP integration when a user connects their GitHub account.
        """
        if created and instance.access_token:
            try:
                # Import here to avoid circular imports
                from .models import MCPUserIntegration
                
                # Create or update MCP integration for this user
                MCPUserIntegration.objects.update_or_create(
                    user=instance.user,
                    defaults={
                        'is_active': True,
                        'last_synced': None,
                    }
                )
                logger.info(f"MCP integration enabled for user {instance.user.id}")
                
            except Exception as e:
                logger.error(f"Failed to set up MCP integration for user {instance.user.id}: {str(e)}")

    @receiver(post_save, sender=GitHubUser)
    def cleanup_mcp_integration(sender, instance, **kwargs):
        """
        Clean up MCP integration if GitHub account is disconnected.
        """
        if not instance.access_token:  # Access token was removed
            try:
                from .models import MCPUserIntegration
                MCPUserIntegration.objects.filter(user=instance.user).update(is_active=False)
                logger.info(f"MCP integration disabled for user {instance.user.id}")
            except Exception as e:
                logger.error(f"Failed to clean up MCP integration for user {instance.user.id}: {str(e)}")
else:
    logger.warning("GitHubUser model not found. MCP integration signals will not be registered.")