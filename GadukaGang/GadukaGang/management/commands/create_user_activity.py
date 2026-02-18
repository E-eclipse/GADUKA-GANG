from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random
from GadukaGang.models import (
    User, Section, Topic, Post, Community, CommunityMembership
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Создает активность пользователей для наполнения аналитики'

    def handle(self, *args, **options):
        self.stdout.write('Создаем активность пользователей...')
        
        # Создаем дополнительные темы и сообщения
        self.create_additional_topics_and_posts()
        
        # Обновляем даты активности
        self.update_activity_dates()
        
        self.stdout.write(self.style.SUCCESS('Активность пользователей создана!'))

    def create_additional_topics_and_posts(self):
        """Создаем дополнительные темы и сообщения с разными датами"""
        self.stdout.write('Создаем дополнительные темы и сообщения...')
        
        users = list(User.objects.all())
        sections = list(Section.objects.all())
        communities = list(Community.objects.all())
        
        topics_created = 0
        posts_created = 0
        
        # Создаем дополнительные темы в разделах
        for i in range(20):  # Создаем 20 дополнительных тем
            author = random.choice(users)
            section = random.choice(sections)
            
            # Разные даты создания в прошлом
            days_ago = random.randint(1, 120)  # В пределах последних 4 месяцев
            hours_ago = random.randint(0, 23)
            created_date = timezone.now() - timedelta(days=days_ago, hours=hours_ago)
            
            topic = Topic.objects.create(
                section=section,
                title=f'Дополнительная тема #{i+1} от {author.username}',
                author=author,
                created_date=created_date,
                last_post_date=created_date
            )
            topics_created += 1
            
            # Создаем первое сообщение в теме
            post_content = f'Это первое сообщение в теме "{topic.title}". Здесь пользователь {author.username} делится своими мыслями.'
            post = Post.objects.create(
                topic=topic,
                author=author,
                content=post_content,
                created_date=created_date
            )
            posts_created += 1
            
            # Создаем дополнительные сообщения в теме
            num_posts = random.randint(0, 15)  # До 15 дополнительных сообщений
            for j in range(num_posts):
                poster = random.choice(users)
                # Даты ответов позже даты создания темы
                post_days_ago = max(0, days_ago - random.randint(0, min(30, days_ago)))
                post_hours_ago = random.randint(0, 23)
                post_date = timezone.now() - timedelta(days=post_days_ago, hours=post_hours_ago)
                
                post_content = f'Ответ #{j+1} от пользователя {poster.username} на тему "{topic.title}".'
                post = Post.objects.create(
                    topic=topic,
                    author=poster,
                    content=post_content,
                    created_date=post_date
                )
                posts_created += 1
                
                # Обновляем дату последнего сообщения в теме
                if post_date > topic.last_post_date:
                    topic.last_post_date = post_date
                    topic.save()
        
        # Создаем темы в сообществах
        for community in communities:
            members = list(CommunityMembership.objects.filter(community=community).select_related('user'))
            if not members:
                continue
                
            num_topics = random.randint(2, 8)  # 2-8 тем в каждом сообществе
            for i in range(num_topics):
                author_membership = random.choice(members)
                author = author_membership.user
                
                # Разные даты создания в прошлом
                days_ago = random.randint(1, 90)  # В пределах последних 3 месяцев
                hours_ago = random.randint(0, 23)
                created_date = timezone.now() - timedelta(days=days_ago, hours=hours_ago)
                
                # Используем первый раздел для тем сообществ
                section = sections[0] if sections else None
                if not section:
                    continue
                    
                topic = Topic.objects.create(
                    section=section,
                    title=f'Тема в сообществе {community.name} #{i+1}',
                    author=author,
                    created_date=created_date,
                    last_post_date=created_date
                )
                topics_created += 1
                
                # Связываем тему с сообществом
                from GadukaGang.models import CommunityTopic
                CommunityTopic.objects.create(
                    community=community,
                    topic=topic,
                    created_date=created_date
                )
                
                # Создаем первое сообщение в теме
                post_content = f'Обсуждение в сообществе "{community.name}". Тема: {topic.title}.'
                post = Post.objects.create(
                    topic=topic,
                    author=author,
                    content=post_content,
                    created_date=created_date
                )
                posts_created += 1
                
                # Создаем дополнительные сообщения в теме от участников сообщества
                num_posts = random.randint(0, 10)  # До 10 дополнительных сообщений
                for j in range(num_posts):
                    # Выбираем случайного участника сообщества
                    poster_membership = random.choice(members)
                    poster = poster_membership.user
                    
                    # Даты ответов позже даты создания темы
                    post_days_ago = max(0, days_ago - random.randint(0, min(20, days_ago)))
                    post_hours_ago = random.randint(0, 23)
                    post_date = timezone.now() - timedelta(days=post_days_ago, hours=post_hours_ago)
                    
                    post_content = f'Участник {poster.username} сообщества "{community.name}" делится мнением по теме: {topic.title}.'
                    post = Post.objects.create(
                        topic=topic,
                        author=poster,
                        content=post_content,
                        created_date=post_date
                    )
                    posts_created += 1
                    
                    # Обновляем дату последнего сообщения в теме
                    if post_date > topic.last_post_date:
                        topic.last_post_date = post_date
                        topic.save()
        
        self.stdout.write(self.style.SUCCESS(f'  Создано тем: {topics_created}'))
        self.stdout.write(self.style.SUCCESS(f'  Создано сообщений: {posts_created}'))

    def update_activity_dates(self):
        """Обновляем даты активности для большего разнообразия"""
        self.stdout.write('Обновляем даты активности...')
        
        users = list(User.objects.all())
        
        # Обновляем даты последней активности пользователей
        for user in users:
            # Разные даты последней активности
            days_ago = random.randint(0, 60)  # В пределах последних 2 месяцев
            hours_ago = random.randint(0, 23)
            last_activity = timezone.now() - timedelta(days=days_ago, hours=hours_ago)
            
            try:
                profile = user.userprofile
                profile.last_activity = last_activity
                profile.save(update_fields=['last_activity'])
            except:
                pass  # Игнорируем ошибки, если профиль не существует
        
        # Обновляем даты создания для существующих тем и сообщений
        # (в реальном приложении это лучше делать через миграции или прямые SQL запросы)
        
        self.stdout.write(self.style.SUCCESS('  Даты активности обновлены'))