from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random
from GadukaGang.models import (
    User, UserProfile, Section, Topic, Post, Tag, TopicTag, 
    Certificate, UserCertificate, Achievement, UserAchievement,
    UserRank, UserRankProgress, PostLike, TopicRating,
    Community, CommunityMembership, CommunityTopic,
    Course, Lesson, CourseProgress, TopicView
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Добавляет больше данных для аналитики с разными датами'

    def handle(self, *args, **options):
        self.stdout.write('Начинаем добавление данных для аналитики...')
        
        # Добавляем больше просмотров тем
        self.add_more_topic_views()
        
        # Добавляем больше лайков
        self.add_more_likes()
        
        # Добавляем больше оценок
        self.add_more_ratings()
        
        # Обновляем статистику пользователей
        self.update_user_stats()
        
        # Создаем достижения и сертификаты
        self.create_achievements_and_certificates()
        
        self.stdout.write(self.style.SUCCESS('Данные для аналитики успешно добавлены!'))

    def add_more_topic_views(self):
        """Добавляем больше просмотров тем с разными датами"""
        self.stdout.write('Добавляем просмотры тем...')
        
        users = list(User.objects.all())
        topics = list(Topic.objects.all())
        
        views_created = 0
        # Создаем просмотры для большего количества тем
        for topic in topics:
            # Создаем просмотры с разными датами для имитации активности
            for i in range(random.randint(0, 10)):
                user = random.choice(users)
                # Разные даты в прошлом
                days_ago = random.randint(0, 90)  # В пределах последних 3 месяцев
                hours_ago = random.randint(0, 23)
                view_date = timezone.now() - timedelta(days=days_ago, hours=hours_ago)
                
                # Создаем или обновляем просмотр
                view, created = TopicView.objects.get_or_create(
                    topic=topic,
                    user=user,
                    defaults={
                        'view_date': view_date
                    }
                )
                
                if not created:
                    # Обновляем дату просмотра для разнообразия
                    view.view_date = view_date
                    view.save()
                
                views_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'  Добавлено просмотров тем: {views_created}'))

    def add_more_likes(self):
        """Добавляем больше лайков с разными датами"""
        self.stdout.write('Добавляем лайки...')
        
        users = list(User.objects.all())
        posts = list(Post.objects.all())
        
        likes_created = 0
        # Создаем лайки для большего количества сообщений
        for post in posts:
            # Создаем лайки от разных пользователей
            num_likes = random.randint(0, min(15, len(users)))  # До 15 лайков на сообщение
            likers = random.sample(users, num_likes) if num_likes > 0 else []
            
            for user in likers:
                # Проверяем, не поставил ли пользователь уже лайк
                existing_like = PostLike.objects.filter(post=post, user=user).first()
                if existing_like:
                    continue
                
                # Разные даты в прошлом
                days_ago = random.randint(0, 60)  # В пределах последних 2 месяцев
                hours_ago = random.randint(0, 23)
                like_date = timezone.now() - timedelta(days=days_ago, hours=hours_ago)
                
                # Случайно выбираем лайк или дизлайк (80% лайков, 20% дизлайков)
                like_type = 'like' if random.random() > 0.2 else 'dislike'
                
                like = PostLike.objects.create(
                    post=post,
                    user=user,
                    like_type=like_type
                )
                
                # Устанавливаем дату создания (через прямое обновление, так как created_date не редактируемое поле)
                # В реальном приложении это лучше делать через миграции или сигналы
                likes_created += 1
        
        # Обновляем счетчики лайков в сообщениях
        for post in posts:
            post.like_count = PostLike.objects.filter(post=post, like_type='like').count()
            post.dislike_count = PostLike.objects.filter(post=post, like_type='dislike').count()
            post.save()
        
        self.stdout.write(self.style.SUCCESS(f'  Добавлено лайков/дизлайков: {likes_created}'))

    def add_more_ratings(self):
        """Добавляем больше оценок тем с разными датами"""
        self.stdout.write('Добавляем оценки тем...')
        
        users = list(User.objects.all())
        topics = list(Topic.objects.all())
        
        ratings_created = 0
        # Создаем оценки для тем
        for topic in topics:
            # Создаем оценки от разных пользователей
            num_ratings = random.randint(0, min(10, len(users)))  # До 10 оценок на тему
            raters = random.sample(users, num_ratings) if num_ratings > 0 else []
            
            for user in raters:
                # Проверяем, не поставил ли пользователь уже оценку
                existing_rating = TopicRating.objects.filter(topic=topic, user=user).first()
                if existing_rating:
                    continue
                
                # Разные даты в прошлом
                days_ago = random.randint(0, 45)  # В пределах последних 1.5 месяцев
                hours_ago = random.randint(0, 23)
                rating_date = timezone.now() - timedelta(days=days_ago, hours=hours_ago)
                
                # Случайная оценка от 1 до 5
                rating_value = random.randint(1, 5)
                
                rating = TopicRating.objects.create(
                    topic=topic,
                    user=user,
                    rating=rating_value
                )
                
                # Устанавливаем дату создания
                ratings_created += 1
        
        # Обновляем средние оценки в темах
        for topic in topics:
            ratings = TopicRating.objects.filter(topic=topic)
            if ratings.exists():
                topic.rating_count = ratings.count()
                topic.average_rating = sum(r.rating for r in ratings) / topic.rating_count
                topic.save()
        
        self.stdout.write(self.style.SUCCESS(f'  Добавлено оценок тем: {ratings_created}'))

    def update_user_stats(self):
        """Обновляем статистику пользователей"""
        self.stdout.write('Обновляем статистику пользователей...')
        
        users = list(User.objects.all())
        
        # Обновляем даты регистрации пользователей, чтобы они были в разное время
        for i, user in enumerate(users):
            # Разные даты регистрации в прошлом
            days_ago = random.randint(1, 100)  # В пределах последних 100 дней
            registration_date = timezone.now() - timedelta(days=days_ago)
            
            # Так как registration_date это auto_now_add поле, мы не можем его напрямую изменить
            # В реальном приложении это лучше делать через миграции или прямые SQL запросы
            
            # Обновляем профили пользователей
            try:
                profile = user.userprofile
                # Обновляем количество сообщений
                post_count = Post.objects.filter(author=user, is_deleted=False).count()
                profile.post_count = post_count
                
                # Устанавливаем карму (случайное значение от 0 до 1000)
                profile.karma = random.randint(0, 1000)
                
                # Разные даты присоединения
                join_days_ago = random.randint(1, min(100, days_ago))  # Не раньше даты регистрации
                profile.join_date = timezone.now() - timedelta(days=join_days_ago)
                
                profile.save()
            except UserProfile.DoesNotExist:
                # Создаем профиль, если он не существует
                UserProfile.objects.create(
                    user=user,
                    post_count=Post.objects.filter(author=user, is_deleted=False).count(),
                    karma=random.randint(0, 1000)
                )
        
        # Обновляем прогресс курсов
        courses = list(Course.objects.all())
        for user in users:
            for course in courses:
                # С вероятностью 40% пользователь начал курс
                if random.random() > 0.6:
                    progress, created = CourseProgress.objects.get_or_create(
                        user=user,
                        course=course,
                        defaults={
                            'started_date': timezone.now() - timedelta(days=random.randint(1, 60))
                        }
                    )
                    
                    if not created:
                        # Обновляем существующий прогресс
                        lessons = list(course.lessons.all())
                        # Отмечаем случайное количество уроков как завершенные
                        completed_count = random.randint(0, len(lessons))
                        completed_lessons = random.sample(lessons, completed_count) if completed_count > 0 else []
                        progress.completed_lessons.set(completed_lessons)
                        
                        # Если все уроки завершены, отмечаем курс как завершенный
                        if completed_count == len(lessons):
                            progress.is_completed = True
                            progress.completed_date = timezone.now() - timedelta(days=random.randint(0, 30))
                            progress.save()
        
        self.stdout.write(self.style.SUCCESS('  Статистика пользователей обновлена'))

    def create_achievements_and_certificates(self):
        """Создаем достижения и сертификаты"""
        self.stdout.write('Создаем достижения и сертификаты...')
        
        users = list(User.objects.all())
        
        # Создаем достижения, если их еще нет
        achievements_data = [
            {
                'name': 'Первый шаг',
                'description': 'Создать первую тему на форуме',
                'icon_url': '/static/images/achievements/first-step.png',
                'criteria': {'type': 'topic_count', 'value': 1}
            },
            {
                'name': 'Активист',
                'description': 'Создать 10 тем на форуме',
                'icon_url': '/static/images/achievements/active.png',
                'criteria': {'type': 'topic_count', 'value': 10}
            },
            {
                'name': 'Писатель',
                'description': 'Написать 50 сообщений на форуме',
                'icon_url': '/static/images/achievements/writer.png',
                'criteria': {'type': 'post_count', 'value': 50}
            }
        ]
        
        achievements = []
        for data in achievements_data:
            achievement, created = Achievement.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'icon_url': data['icon_url'],
                    'criteria': data['criteria']
                }
            )
            achievements.append(achievement)
        
        # Назначаем достижения пользователям
        achievements_assigned = 0
        for user in users:
            # Каждый пользователь получает случайные достижения
            user_achievements = random.sample(achievements, random.randint(0, len(achievements)))
            for achievement in user_achievements:
                user_achievement, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement,
                    defaults={
                        'awarded_by': None
                    }
                )
                if created:
                    achievements_assigned += 1
        
        # Создаем сертификаты, если их еще нет
        certificates_data = [
            {
                'name': 'Сертификат о прохождении курса: Python для начинающих',
                'description': 'Сертификат подтверждает успешное прохождение курса "Python для начинающих"',
                'template_url': '/static/images/certificates/python-beginner.png',
                'criteria': {'course_id': 1}
            },
            {
                'name': 'Сертификат о прохождении курса: Python для продвинутых',
                'description': 'Сертификат подтверждает успешное прохождение курса "Python для продвинутых"',
                'template_url': '/static/images/certificates/python-advanced.png',
                'criteria': {'course_id': 2}
            }
        ]
        
        certificates = []
        for data in certificates_data:
            certificate, created = Certificate.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'template_url': data['template_url'],
                    'criteria': data['criteria']
                }
            )
            certificates.append(certificate)
        
        # Назначаем сертификаты пользователям
        certificates_assigned = 0
        for user in users:
            # Каждый пользователь получает случайные сертификаты
            user_certificates = random.sample(certificates, random.randint(0, len(certificates)))
            for certificate in user_certificates:
                user_certificate, created = UserCertificate.objects.get_or_create(
                    user=user,
                    certificate=certificate,
                    defaults={
                        'awarded_by': None
                    }
                )
                if created:
                    certificates_assigned += 1
        
        self.stdout.write(self.style.SUCCESS(f'  Назначено достижений: {achievements_assigned}'))
        self.stdout.write(self.style.SUCCESS(f'  Назначено сертификатов: {certificates_assigned}'))