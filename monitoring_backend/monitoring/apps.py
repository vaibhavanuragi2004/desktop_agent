"""
App configuration for the monitoring application
"""

from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    """Configuration for the monitoring app"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitoring'
    verbose_name = 'Desktop Monitoring'
    
    def ready(self):
        """Import signal handlers when the app is ready"""
        import monitoring.models  # This will register the signal handlers
