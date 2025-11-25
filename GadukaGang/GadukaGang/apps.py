from django.apps import AppConfig


class GadukaGangConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'GadukaGang'
    
    def ready(self):
        import GadukaGang.signals
        from . import prometheus_metrics

        prometheus_metrics.initialize_custom_metrics()