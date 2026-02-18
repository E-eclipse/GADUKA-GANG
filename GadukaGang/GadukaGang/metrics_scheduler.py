"""
Модуль для автоматического сбора метрик InfluxDB по расписанию.
"""
import logging
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# Глобальный планировщик
_scheduler = None


def start_metrics_scheduler():
    """
    Запускает планировщик для автоматического сбора метрик InfluxDB.
    Метрики собираются каждые 18 секунд.
    """
    global _scheduler
    
    from django.conf import settings
    if not getattr(settings, 'INFLUXDB_ENABLED', False):
        logger.info("InfluxDB metrics disabled; scheduler not started.")
        return

    if _scheduler is not None and _scheduler.running:
        logger.warning("Metrics scheduler is already running")
        return
    
    _scheduler = BackgroundScheduler()
    
    # Добавляем задачу на сбор метрик каждые 18 секунд
    _scheduler.add_job(
        write_metrics_job,
        trigger=IntervalTrigger(seconds=18),
        id='influxdb_metrics_job',
        name='Write InfluxDB metrics every 18 seconds',
        replace_existing=True,
    )
    
    try:
        logger.info("Starting InfluxDB metrics scheduler...")
        _scheduler.start()
        logger.info("InfluxDB metrics scheduler started successfully (interval: 18 seconds)")
        
        # Регистрируем остановку планировщика при выходе
        atexit.register(lambda: _scheduler.shutdown() if _scheduler else None)
    except Exception as e:
        logger.error(f"Error starting metrics scheduler: {e}", exc_info=True)
        raise


def write_metrics_job():
    """
    Задача для записи метрик в InfluxDB.
    Вызывается планировщиком каждые 18 секунд.
    """
    from django.conf import settings
    if not getattr(settings, 'INFLUXDB_ENABLED', False):
        return
    try:
        from .metrics import InfluxMetricsWriter
        
        metrics_writer = InfluxMetricsWriter()
        metrics_writer.write_all_metrics()
        metrics_writer.close()
        
        logger.debug("InfluxDB metrics written successfully")
    except Exception as e:
        logger.error(f"Error writing InfluxDB metrics: {e}", exc_info=True)

