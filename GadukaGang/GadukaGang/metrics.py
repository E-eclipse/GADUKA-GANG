import os
import math
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
from django.utils import timezone
from django.conf import settings
from datetime import timedelta


class InfluxMetricsWriter:
    # Класс для записи метрик в InfluxDB

    def __init__(self):
        # Инициализация клиента InfluxDB.
        self.token = os.environ.get(
            "INFLUXDB_TOKEN",
            getattr(settings, 'INFLUXDB_TOKEN', '')
        )
        self.org = os.environ.get(
            "INFLUXDB_ORG",
            getattr(settings, 'INFLUXDB_ORG', 'MPT')
        )
        self.url = os.environ.get(
            "INFLUXDB_URL",
            getattr(settings, 'INFLUXDB_URL', 'http://host.docker.internal:8086')
        )
        self.bucket = os.environ.get(
            "INFLUXDB_BUCKET",
            getattr(settings, 'INFLUXDB_BUCKET', 'metrics')
        )
        
        self.client = influxdb_client.InfluxDBClient(
            url=self.url,
            token=self.token,
            org=self.org
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def write_active_users(self):
        # Запись метрики по количеству активных пользователей.
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Получаем количество активных пользователей
        active_users_count = User.objects.filter(is_active=True).count()
        
        # Записываем данные в InfluxDB (округляем в большую сторону до целого)
        point = (
            influxdb_client.Point("gaduka_active_users")
            .field("total", float(math.ceil(active_users_count)))
        )
        self.write_api.write(bucket=self.bucket, org=self.org, record=point)

    def write_communities(self):
        # Запись метрики по количеству сообществ.
        from .models import Community
        
        # Получаем количество сообществ
        communities_count = Community.objects.count()
        
        # Записываем данные в InfluxDB (округляем в большую сторону до целого)
        point = (
            influxdb_client.Point("gaduka_communities")
            .field("total", float(math.ceil(communities_count)))
        )
        self.write_api.write(bucket=self.bucket, org=self.org, record=point)

    def write_posts(self):
        # Запись метрики по количеству постов.
        from .models import Post
        
        # Получаем количество постов (без удаленных)
        posts_count = Post.objects.filter(is_deleted=False).count()
        
        # Записываем данные в InfluxDB (округляем в большую сторону до целого)
        point = (
            influxdb_client.Point("gaduka_posts")
            .field("total", float(math.ceil(posts_count)))
        )
        self.write_api.write(bucket=self.bucket, org=self.org, record=point)

    def write_hot_topics(self):
        # Запись метрики по количеству горячих тем (с новыми постами за последние 24 часа).
        from .models import Topic

        # Получаем количество тем с новыми постами за последние 24 часа
        window_start = timezone.now() - timedelta(hours=24)
        hot_topics_count = Topic.objects.filter(last_post_date__gte=window_start).count()
        
        # Записываем данные в InfluxDB (округляем в большую сторону до целого)
        point = (
            influxdb_client.Point("gaduka_hot_topics")
            .field("total", float(math.ceil(hot_topics_count)))
        )
        self.write_api.write(bucket=self.bucket, org=self.org, record=point)

    def write_all_metrics(self):
        # Создал функцию для записи всех метрик сразу вместо каждой по отдельности
        self.write_active_users()
        self.write_communities()
        self.write_posts()
        self.write_hot_topics()

    def close(self):
        # Закрытие соединения InfluxDB (чтобы ничего не полетело)
        self.write_api.close()
        self.client.close()