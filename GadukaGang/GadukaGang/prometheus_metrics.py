from datetime import timedelta

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save
from django.db.utils import OperationalError, ProgrammingError
from django.dispatch import receiver
from django.utils import timezone
from prometheus_client import Gauge


User = get_user_model()
Community = apps.get_model('GadukaGang', 'Community')
Post = apps.get_model('GadukaGang', 'Post')
Topic = apps.get_model('GadukaGang', 'Topic')

active_users_gauge = Gauge(
    'gaduka_active_users_total',
    'Количество активных пользователей в GadukaGang'
)
communities_gauge = Gauge(
    'gaduka_communities_total',
    'Количество сообществ доступных пользователям'
)
posts_gauge = Gauge(
    'gaduka_posts_total',
    'Количество постов опубликованных на форуме'
)
hot_topics_gauge = Gauge(
    'gaduka_hot_topics_total',
    'Количество тем с новыми постами за последние 24 часа'
)


def _safe_set_gauge(gauge, value_getter):
    try:
        gauge.set(value_getter())
    except (OperationalError, ProgrammingError):
        pass


def refresh_user_metrics():
    _safe_set_gauge(active_users_gauge, lambda: User.objects.filter(is_active=True).count())


def refresh_community_metrics():
    _safe_set_gauge(communities_gauge, lambda: Community.objects.count())


def refresh_post_metrics():
    _safe_set_gauge(posts_gauge, lambda: Post.objects.filter(is_deleted=False).count())


def refresh_hot_topic_metrics():
    window_start = timezone.now()
    _safe_set_gauge(hot_topics_gauge, lambda: Topic.objects.filter(last_post_date__gte=window_start).count())


@receiver(post_save, sender=User)
@receiver(post_delete, sender=User)
def handle_user_change(**kwargs):
    refresh_user_metrics()


@receiver(post_save, sender=Community)
@receiver(post_delete, sender=Community)
def handle_community_change(**kwargs):
    refresh_community_metrics()


@receiver(post_save, sender=Post)
@receiver(post_delete, sender=Post)
def handle_post_change(**kwargs):
    refresh_post_metrics()
    refresh_hot_topic_metrics()


@receiver(post_save, sender=Topic)
@receiver(post_delete, sender=Topic)
def handle_topic_change(**kwargs):
    refresh_hot_topic_metrics()


def initialize_custom_metrics():
    """
    Populate gauges with actual data once the app registry is ready.
    This keeps metric values consistent after process restarts.
    """
    refresh_user_metrics()
    refresh_community_metrics()
    refresh_post_metrics()
    refresh_hot_topic_metrics()


