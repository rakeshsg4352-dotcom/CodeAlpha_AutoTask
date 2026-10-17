from django.apps import AppConfig


class AutomationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'automation'
    verbose_name = 'Task Automation System'

    def ready(self):
        # Ensure default media directories exist upon application initialization
        import os
        from django.conf import settings
        
        directories = [
            settings.MEDIA_ROOT,
            os.path.join(settings.MEDIA_ROOT, 'generated'),
            os.path.join(settings.MEDIA_ROOT, 'uploads'),
            os.path.join(settings.MEDIA_ROOT, 'workspace'),
            os.path.join(settings.MEDIA_ROOT, 'workspace', 'source_sample'),
            os.path.join(settings.MEDIA_ROOT, 'workspace', 'destination'),
        ]
        for dir_path in directories:
            try:
                os.makedirs(dir_path, exist_ok=True)
            except Exception:
                pass
