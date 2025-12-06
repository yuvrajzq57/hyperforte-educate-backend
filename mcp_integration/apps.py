from django.apps import AppConfig

class MCPIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mcp_integration'

    def ready(self):
        # Import and register signals when the app is ready
        from . import signals  # noqa
