from django.apps import AppConfig


class GadukaGangConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'GadukaGang'
    
    def ready(self):
        import GadukaGang.signals
        
        # Запускаем автоматический сбор метрик InfluxDB каждые 18 секунд
        # Запускаем только в основном процессе (не в миграциях и т.д.)
        import sys
        
        # Список команд, при которых НЕ нужно запускать планировщик
        skip_commands = ['migrate', 'makemigrations', 'collectstatic', 'shell', 'test', 'flush']
        
        # Проверяем, что это не команда управления, которая не должна запускать планировщик
        should_start = True
        for arg in sys.argv:
            if any(cmd in arg for cmd in skip_commands):
                should_start = False
                break
        
        if should_start:
            try:
                from django.conf import settings
                if not getattr(settings, 'INFLUXDB_ENABLED', False):
                    return
                from .metrics_scheduler import start_metrics_scheduler
                start_metrics_scheduler()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Ошибка запуска планировщика: {e}")
