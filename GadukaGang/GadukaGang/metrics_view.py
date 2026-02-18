from django.http import HttpResponse
from .metrics import InfluxMetricsWriter


def influx_metrics_view(_request):
    # View для записи метрик в InfluxDB.
    try:
        # Создаем экземпляр класса для записи метрик
        metrics_writer = InfluxMetricsWriter()
        
        # Записываем все метрики
        metrics_writer.write_all_metrics()
        
        # Закрываем соединение
        metrics_writer.close()
        
        # Возвращаем успешный ответ
        response_content = "Метрики успешно записаны в InfluxDB"
        return HttpResponse(response_content.encode('utf-8'), content_type="text/plain")
    except Exception as e:
        # В случае ошибки возвращаем сообщение об ошибке
        response_content = f"Ошибка записи метрик в InfluxDB: {str(e)}"
        return HttpResponse(response_content.encode('utf-8'), content_type="text/plain", status=500)