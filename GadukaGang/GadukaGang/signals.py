from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Count
from .models import Post, UserAchievement, Achievement, UserRankProgress
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=Post)
def check_post_achievements(sender, instance, created, **kwargs):
    """Проверяет и выдает достижения, связанные с созданием сообщений"""
    if created and not instance.is_deleted:
        user = instance.author
        
        # Подсчитываем количество сообщений пользователя
        post_count = Post.objects.filter(author=user, is_deleted=False).count()
        
        # Проверяем достижения, связанные с количеством сообщений
        post_achievements = Achievement.objects.filter(criteria__type='post_count')
        
        for achievement in post_achievements:
            criteria_value = achievement.criteria.get('value', 0)
            # Проверяем, достиг ли пользователь необходимого количества сообщений
            if post_count >= criteria_value:
                # Проверяем, не получил ли пользователь это достижение ранее
                if not UserAchievement.objects.filter(user=user, achievement=achievement).exists():
                    # Выдаем достижение
                    UserAchievement.objects.create(
                        user=user,
                        achievement=achievement,
                        awarded_by=None  # Системное вручение
                    )
                    # Увеличиваем очки ранга
                    try:
                        rank_progress = UserRankProgress.objects.get(user=user)
                        rank_progress.current_points += 10
                        rank_progress.save()
                    except UserRankProgress.DoesNotExist:
                        # Если нет записи о прогрессе, создаем ее
                        UserRankProgress.objects.create(
                            user=user,
                            current_points=10,
                            progress_percentage=0
                        )


def check_upvotes_achievements(user):
    """Проверяет и выдает достижения, связанные с положительными оценками"""
    # Подсчитываем количество лайков у всех сообщений пользователя
    from .models import PostLike
    
    upvotes_count = PostLike.objects.filter(
        post__author=user,
        like_type='like'
    ).count()
    
    # Проверяем достижения, связанные с количеством лайков
    upvotes_achievements = Achievement.objects.filter(criteria__type='upvotes')
    
    for achievement in upvotes_achievements:
        criteria_value = achievement.criteria.get('value', 0)
        # Проверяем, достиг ли пользователь необходимого количества лайков
        if upvotes_count >= criteria_value:
            # Проверяем, не получил ли пользователь это достижение ранее
            if not UserAchievement.objects.filter(user=user, achievement=achievement).exists():
                # Выдаем достижение
                UserAchievement.objects.create(
                    user=user,
                    achievement=achievement,
                    awarded_by=None  # Системное вручение
                )
                # Увеличиваем очки ранга
                try:
                    rank_progress = UserRankProgress.objects.get(user=user)
                    rank_progress.current_points += 10
                    rank_progress.save()
                except UserRankProgress.DoesNotExist:
                    # Если нет записи о прогрессе, создаем ее
                    UserRankProgress.objects.create(
                        user=user,
                        current_points=10,
                        progress_percentage=0
                    )


def check_topic_achievements(user):
    """Проверяет и выдает достижения, связанные с созданием тем"""
    from .models import Topic
    
    # Подсчитываем количество тем пользователя
    topic_count = Topic.objects.filter(author=user).count()
    
    # Проверяем достижения, связанные с созданием первой темы
    if topic_count >= 1:
        try:
            first_topic_achievement = Achievement.objects.get(name="Первый шаг")
            # Проверяем, не получил ли пользователь это достижение ранее
            if not UserAchievement.objects.filter(user=user, achievement=first_topic_achievement).exists():
                # Выдаем достижение
                UserAchievement.objects.create(
                    user=user,
                    achievement=first_topic_achievement,
                    awarded_by=None  # Системное вручение
                )
                # Увеличиваем очки ранга
                try:
                    rank_progress = UserRankProgress.objects.get(user=user)
                    rank_progress.current_points += 10
                    rank_progress.save()
                except UserRankProgress.DoesNotExist:
                    # Если нет записи о прогрессе, создаем ее
                    UserRankProgress.objects.create(
                        user=user,
                        current_points=10,
                        progress_percentage=0
                    )
        except Achievement.DoesNotExist:
            # Если достижение "Первый шаг" не существует, создаем его
            first_topic_achievement = Achievement.objects.create(
                name="Первый шаг",
                description="Создать первую тему на форуме",
                icon_url="/static/images/achievements/first-step.png",
                criteria={"type": "topic_count", "value": 1}
            )
            # Выдаем достижение
            UserAchievement.objects.create(
                user=user,
                achievement=first_topic_achievement,
                awarded_by=None  # Системное вручение
            )
            # Увеличиваем очки ранга
            try:
                rank_progress = UserRankProgress.objects.get(user=user)
                rank_progress.current_points += 10
                rank_progress.save()
            except UserRankProgress.DoesNotExist:
                # Если нет записи о прогрессе, создаем ее
                UserRankProgress.objects.create(
                    user=user,
                    current_points=10,
                    progress_percentage=0
                )