from django.apps import AppConfig

class JobMatchingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'job_matching'

    def ready(self):
        import job_matching.signals  # noqa