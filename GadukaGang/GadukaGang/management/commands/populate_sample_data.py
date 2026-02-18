from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random
from GadukaGang.models import (
    User, UserProfile, Section, Topic, Post, Tag, TopicTag, 
    Certificate, UserCertificate, Achievement, UserAchievement,
    UserRank, UserRankProgress, PostLike, TopicRating,
    Community, CommunityMembership, CommunityTopic
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми данными'

    def handle(self, *args, **options):
        self.stdout.write('Начинаем заполнение базы данных...')
        
        # Создаем пользователей
        self.create_users()
        
        # Создаем разделы форума
        self.create_sections()
        
        # Создаем теги
        self.create_tags()
        
        # Создаем сообщества
        self.create_communities()
        
        # Создаем темы и сообщения
        self.create_topics_and_posts()
        
        # Создаем достижения
        self.create_achievements()
        
        # Создаем сертификаты
        self.create_certificates()
        
        # Создаем ранги пользователей
        self.create_user_ranks()
        
        # Назначаем достижения пользователям
        self.assign_achievements()
        
        # Назначаем сертификаты пользователям
        self.assign_certificates()
        
        # Создаем лайки и оценки
        self.create_likes_and_ratings()
        
        self.stdout.write(self.style.SUCCESS('База данных успешно заполнена тестовыми данными!'))

    def create_users(self):
        """Создаем 8 пользователей с разными ролями"""
        self.stdout.write('Создаем пользователей...')
        
        user_data = [
            {
                'username': 'admin',
                'email': 'admin@gadukagang.com',
                'first_name': 'Админ',
                'last_name': 'Главный',
                'role': 'super_admin',
                'bio': 'Администратор системы Gaduka Gang',
                'signature': 'Администрация форума'
            },
            {
                'username': 'moderator1',
                'email': 'mod1@gadukagang.com',
                'first_name': 'Модератор',
                'last_name': 'Первый',
                'role': 'moderator',
                'bio': 'Модератор форума',
                'signature': 'Модераторская подпись'
            },
            {
                'username': 'moderator2',
                'email': 'mod2@gadukagang.com',
                'first_name': 'Модератор',
                'last_name': 'Второй',
                'role': 'moderator',
                'bio': 'Модератор форума',
                'signature': 'Модераторская подпись'
            },
            {
                'username': 'user1',
                'email': 'user1@gadukagang.com',
                'first_name': 'Иван',
                'last_name': 'Петров',
                'role': 'user',
                'bio': 'Активный участник форума',
                'signature': 'Подпись пользователя 1'
            },
            {
                'username': 'user2',
                'email': 'user2@gadukagang.com',
                'first_name': 'Мария',
                'last_name': 'Сидорова',
                'role': 'user',
                'bio': 'Новичок на форуме',
                'signature': 'Подпись пользователя 2'
            },
            {
                'username': 'user3',
                'email': 'user3@gadukagang.com',
                'first_name': 'Алексей',
                'last_name': 'Иванов',
                'role': 'user',
                'bio': 'Программист Python',
                'signature': 'Python forever!'
            },
            {
                'username': 'user4',
                'email': 'user4@gadukagang.com',
                'first_name': 'Елена',
                'last_name': 'Козлова',
                'role': 'user',
                'bio': 'Изучаю веб-разработку',
                'signature': 'Frontend developer'
            },
            {
                'username': 'user5',
                'email': 'user5@gadukagang.com',
                'first_name': 'Дмитрий',
                'last_name': 'Смирнов',
                'role': 'user',
                'bio': 'Интересуюсь кибербезопасностью',
                'signature': 'Security researcher'
            }
        ]
        
        self.users = []
        for i, data in enumerate(user_data):
            # Создаем пользователя
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'role': data['role'],
                    'is_active': True,
                    'is_staff': data['role'] in ['super_admin', 'admin_level_1', 'admin_level_2', 'admin_level_3'],
                    'is_superuser': data['role'] == 'super_admin'
                }
            )
            
            if created:
                # Устанавливаем пароль
                user.set_password('password123')
                user.save()
                
                # Создаем профиль пользователя
                UserProfile.objects.create(
                    user=user,
                    bio=data['bio'],
                    signature=data['signature'],
                    post_count=0
                )
                
                # Создаем прогресс ранга
                UserRankProgress.objects.create(
                    user=user,
                    current_points=random.randint(0, 1000),
                    progress_percentage=random.randint(0, 100)
                )
                
                self.stdout.write(self.style.SUCCESS(f'  Создан пользователь: {user.username}'))
            else:
                self.stdout.write(self.style.WARNING(f'  Пользователь уже существует: {user.username}'))
            
            self.users.append(user)
        
        self.stdout.write(self.style.SUCCESS(f'Создано {len(self.users)} пользователей'))

    def create_sections(self):
        """Создаем разделы форума"""
        self.stdout.write('Создаем разделы форума...')
        
        sections_data = [
            {
                'name': 'Общие вопросы',
                'description': 'Обсуждение общих вопросов, не относящихся к другим разделам'
            },
            {
                'name': 'Python',
                'description': 'Все о языке программирования Python'
            },
            {
                'name': 'Веб-разработка',
                'description': 'Фронтенд и бэкенд разработка веб-приложений'
            },
            {
                'name': 'Базы данных',
                'description': 'Реляционные и нереляционные базы данных'
            },
            {
                'name': 'Кибербезопасность',
                'description': 'Защита информации и сетевая безопасность'
            },
            {
                'name': 'Мобильная разработка',
                'description': 'Разработка мобильных приложений'
            }
        ]
        
        self.sections = []
        for data in sections_data:
            section, created = Section.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'created_by': random.choice(self.users)
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Создан раздел: {section.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'  Раздел уже существует: {section.name}'))
            
            self.sections.append(section)
        
        self.stdout.write(self.style.SUCCESS(f'Создано {len(self.sections)} разделов'))

    def create_tags(self):
        """Создаем теги"""
        self.stdout.write('Создаем теги...')
        
        tags_data = [
            {'name': 'python', 'color': '#3572A5'},
            {'name': 'javascript', 'color': '#f1e05a'},
            {'name': 'html', 'color': '#e34c26'},
            {'name': 'css', 'color': '#563d7c'},
            {'name': 'django', 'color': '#092e20'},
            {'name': 'flask', 'color': '#000000'},
            {'name': 'sql', 'color': '#e38c00'},
            {'name': 'nosql', 'color': '#4db33d'},
            {'name': 'security', 'color': '#ff0000'},
            {'name': 'beginner', 'color': '#4caf50'},
            {'name': 'advanced', 'color': '#ff9800'},
            {'name': 'tutorial', 'color': '#2196f3'}
        ]
        
        self.tags = []
        for data in tags_data:
            tag, created = Tag.objects.get_or_create(
                name=data['name'],
                defaults={
                    'color': data['color']
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Создан тег: {tag.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'  Тег уже существует: {tag.name}'))
            
            self.tags.append(tag)
        
        self.stdout.write(self.style.SUCCESS(f'Создано {len(self.tags)} тегов'))

    def create_communities(self):
        """Создаем сообщества (базовые и созданные пользователями)"""
        self.stdout.write('Создаем сообщества...')
        
        # Базовые сообщества
        base_communities = [
            {
                'name': 'Python разработчики',
                'description': 'Сообщество разработчиков на Python',
                'creator': self.users[0],  # admin
                'is_private': False
            },
            {
                'name': 'Веб-мастера',
                'description': 'Сообщество веб-разработчиков',
                'creator': self.users[0],  # admin
                'is_private': False
            },
            {
                'name': 'Кибербезопасность',
                'description': 'Сообщество специалистов по информационной безопасности',
                'creator': self.users[0],  # admin
                'is_private': False
            }
        ]
        
        # Сообщества, созданные пользователями
        user_communities = [
            {
                'name': 'Новички в программировании',
                'description': 'Сообщество для новичков в программировании',
                'creator': self.users[3],  # user1
                'is_private': False
            },
            {
                'name': 'Python для анализа данных',
                'description': 'Сообщество специалистов по анализу данных на Python',
                'creator': self.users[5],  # user3
                'is_private': True  # Приватное сообщество
            },
            {
                'name': 'Фронтенд разработка',
                'description': 'Сообщество фронтенд разработчиков',
                'creator': self.users[6],  # user4
                'is_private': False
            }
        ]
        
        all_communities = base_communities + user_communities
        self.communities = []
        
        for data in all_communities:
            community, created = Community.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'creator': data['creator'],
                    'is_private': data['is_private'],
                    'member_count': 0
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Создано сообщество: {community.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'  Сообщество уже существует: {community.name}'))
            
            self.communities.append(community)
            
            # Добавляем создателя как владельца
            membership, created = CommunityMembership.objects.get_or_create(
                community=community,
                user=data['creator'],
                defaults={
                    'role': 'owner'
                }
            )
            
            if created:
                community.member_count += 1
                community.save()
        
        # Добавляем случайных пользователей в сообщества
        for community in self.communities:
            # Выбираем случайных пользователей для участия
            participants = random.sample(self.users, random.randint(2, len(self.users)-1))
            
            for user in participants:
                # Пропускаем создателя, так как он уже добавлен
                if user == community.creator:
                    continue
                
                # Для приватных сообществ только участники могут присоединяться
                if not community.is_private or user in participants:
                    membership, created = CommunityMembership.objects.get_or_create(
                        community=community,
                        user=user,
                        defaults={
                            'role': 'member' if random.random() > 0.1 else 'moderator'  # 10% становятся модераторами
                        }
                    )
                    
                    if created:
                        community.member_count += 1
                        community.save()
        
        self.stdout.write(self.style.SUCCESS(f'Создано {len(self.communities)} сообществ'))

    def create_topics_and_posts(self):
        """Создаем темы и сообщения"""
        self.stdout.write('Создаем темы и сообщения...')
        
        # Темы для разделов
        topics_data = [
            # Темы для раздела "Общие вопросы"
            {
                'title': 'Правила форума',
                'content': 'Пожалуйста, ознакомьтесь с правилами форума перед началом общения.',
                'section': self.sections[0],
                'author': self.users[0],  # admin
                'tags': ['tutorial'],
                'days_ago': 30
            },
            {
                'title': 'Представьтесь, пожалуйста',
                'content': 'Расскажите немного о себе и ваших интересах в программировании.',
                'section': self.sections[0],
                'author': self.users[0],  # admin
                'tags': ['beginner'],
                'days_ago': 25
            },
            
            # Темы для раздела "Python"
            {
                'title': 'Лучшие практики написания кода на Python',
                'content': 'Какие лучшие практики вы используете при написании кода на Python?',
                'section': self.sections[1],
                'author': self.users[5],  # user3
                'tags': ['python', 'advanced'],
                'days_ago': 20
            },
            {
                'title': 'Как начать изучать Python с нуля?',
                'content': 'Я новичок и хочу начать изучать Python. С чего начать?',
                'section': self.sections[1],
                'author': self.users[4],  # user2
                'tags': ['python', 'beginner'],
                'days_ago': 18
            },
            {
                'title': 'Django vs Flask: что выбрать?',
                'content': 'Сравнение двух популярных фреймворков для Python. Какой лучше?',
                'section': self.sections[1],
                'author': self.users[3],  # user1
                'tags': ['python', 'django', 'flask'],
                'days_ago': 15
            },
            
            # Темы для раздела "Веб-разработка"
            {
                'title': 'Современные фреймворки для фронтенда',
                'content': 'Какие фреймворки вы используете для фронтенд разработки?',
                'section': self.sections[2],
                'author': self.users[6],  # user4
                'tags': ['javascript', 'html', 'css'],
                'days_ago': 12
            },
            {
                'title': 'REST API: лучшие практики проектирования',
                'content': 'Как правильно проектировать REST API для веб-приложений?',
                'section': self.sections[2],
                'author': self.users[5],  # user3
                'tags': ['advanced'],
                'days_ago': 10
            },
            
            # Темы для раздела "Базы данных"
            {
                'title': 'PostgreSQL vs MySQL: сравнение',
                'content': 'Сравнение двух популярных реляционных СУБД.',
                'section': self.sections[3],
                'author': self.users[3],  # user1
                'tags': ['sql'],
                'days_ago': 8
            },
            
            # Темы для раздела "Кибербезопасность"
            {
                'title': 'Основы кибербезопасности для разработчиков',
                'content': 'Какие основные принципы безопасности должен знать каждый разработчик?',
                'section': self.sections[4],
                'author': self.users[7],  # user5
                'tags': ['security'],
                'days_ago': 5
            }
        ]
        
        self.topics = []
        self.posts = []
        
        for topic_data in topics_data:
            # Создаем тему
            created_date = timezone.now() - timedelta(days=topic_data['days_ago'])
            topic = Topic.objects.create(
                section=topic_data['section'],
                title=topic_data['title'],
                author=topic_data['author'],
                created_date=created_date
            )
            
            # Добавляем теги
            for tag_name in topic_data['tags']:
                tag = next((t for t in self.tags if t.name == tag_name), None)
                if tag:
                    TopicTag.objects.create(topic=topic, tag=tag)
            
            self.topics.append(topic)
            self.stdout.write(self.style.SUCCESS(f'  Создана тема: {topic.title}'))
            
            # Создаем первое сообщение в теме
            post = Post.objects.create(
                topic=topic,
                author=topic_data['author'],
                content=topic_data['content'],
                created_date=created_date
            )
            self.posts.append(post)
            
            # Создаем дополнительные сообщения в теме
            num_posts = random.randint(1, 10)
            for i in range(num_posts):
                # Выбираем случайного автора
                author = random.choice(self.users)
                days_ago = topic_data['days_ago'] - random.randint(0, topic_data['days_ago'])
                post_date = timezone.now() - timedelta(days=days_ago)
                
                post_content = f"Это дополнительное сообщение #{i+1} в теме '{topic.title}'. "
                post_content += "Содержание сообщения может варьироваться в зависимости от темы обсуждения. "
                post_content += "Пользователь делится своим мнением и опытом."
                
                post = Post.objects.create(
                    topic=topic,
                    author=author,
                    content=post_content,
                    created_date=post_date
                )
                self.posts.append(post)
        
        # Создаем темы в сообществах
        for community in self.communities:
            num_topics = random.randint(2, 5)
            for i in range(num_topics):
                author = random.choice([m.user for m in CommunityMembership.objects.filter(community=community)])
                days_ago = random.randint(1, 20)
                created_date = timezone.now() - timedelta(days=days_ago)
                
                topic_title = f"Обсуждение в сообществе {community.name} #{i+1}"
                topic_content = f"Это тема обсуждения в сообществе {community.name}. Здесь участники обсуждают различные вопросы, связанные с тематикой сообщества."
                
                # Создаем тему
                topic = Topic.objects.create(
                    section=self.sections[0],  # Используем общий раздел
                    title=topic_title,
                    author=author,
                    created_date=created_date
                )
                
                self.topics.append(topic)
                
                # Связываем тему с сообществом
                CommunityTopic.objects.create(
                    community=community,
                    topic=topic,
                    created_date=created_date
                )
                
                # Создаем первое сообщение
                post = Post.objects.create(
                    topic=topic,
                    author=author,
                    content=topic_content,
                    created_date=created_date
                )
                self.posts.append(post)
                
                # Создаем дополнительные сообщения
                num_posts = random.randint(1, 8)
                for j in range(num_posts):
                    post_author = random.choice([m.user for m in CommunityMembership.objects.filter(community=community)])
                    post_days_ago = days_ago - random.randint(0, days_ago)
                    post_date = timezone.now() - timedelta(days=post_days_ago)
                    
                    post_content = f"Комментарий участника сообщества {community.name} к теме обсуждения. "
                    post_content += "Пользователь делится своим мнением и предлагает решения."
                    
                    post = Post.objects.create(
                        topic=topic,
                        author=post_author,
                        content=post_content,
                        created_date=post_date
                    )
                    self.posts.append(post)
        
        self.stdout.write(self.style.SUCCESS(f'Создано {len(self.topics)} тем и {len(self.posts)} сообщений'))

    def create_achievements(self):
        """Создаем достижения"""
        self.stdout.write('Создаем достижения...')
        
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
            },
            {
                'name': 'Популярный автор',
                'description': 'Получить 100 лайков к своим сообщениям',
                'icon_url': '/static/images/achievements/popular.png',
                'criteria': {'type': 'upvotes', 'value': 100}
            },
            {
                'name': 'Эксперт',
                'description': 'Получить 500 лайков к своим сообщениям',
                'icon_url': '/static/images/achievements/expert.png',
                'criteria': {'type': 'upvotes', 'value': 500}
            },
            {
                'name': 'Ментор',
                'description': 'Помочь 100 пользователям в решении их проблем',
                'icon_url': '/static/images/achievements/mentor.png',
                'criteria': {'type': 'helpful', 'value': 100}
            },
            {
                'name': 'Завершен курс: Python для начинающих',
                'description': 'Вы успешно завершили курс "Python для начинающих"',
                'icon_url': '/static/images/achievements/python-beginner.png',
                'criteria': {'course_id': 1}
            },
            {
                'name': 'Завершен курс: Python для продвинутых',
                'description': 'Вы успешно завершили курс "Python для продвинутых"',
                'icon_url': '/static/images/achievements/python-advanced.png',
                'criteria': {'course_id': 2}
            }
        ]
        
        self.achievements = []
        for data in achievements_data:
            achievement, created = Achievement.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'icon_url': data['icon_url'],
                    'criteria': data['criteria']
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Создано достижение: {achievement.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'  Достижение уже существует: {achievement.name}'))
            
            self.achievements.append(achievement)
        
        self.stdout.write(self.style.SUCCESS(f'Создано {len(self.achievements)} достижений'))

    def create_certificates(self):
        """Создаем сертификаты"""
        self.stdout.write('Создаем сертификаты...')
        
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
            },
            {
                'name': 'Сертификат участия в хакатоне 2025',
                'description': 'Сертификат подтверждает участие в ежегодном хакатоне Gaduka Gang 2025',
                'template_url': '/static/images/certificates/hackathon-2025.png',
                'criteria': {'event': 'hackathon_2025'}
            },
            {
                'name': 'Сертификат модератора',
                'description': 'Сертификат подтверждает статус модератора форума Gaduka Gang',
                'template_url': '/static/images/certificates/moderator.png',
                'criteria': {'role': 'moderator'}
            }
        ]
        
        self.certificates = []
        for data in certificates_data:
            certificate, created = Certificate.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'template_url': data['template_url'],
                    'criteria': data['criteria']
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Создан сертификат: {certificate.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'  Сертификат уже существует: {certificate.name}'))
            
            self.certificates.append(certificate)
        
        self.stdout.write(self.style.SUCCESS(f'Создано {len(self.certificates)} сертификатов'))

    def create_user_ranks(self):
        """Создаем ранги пользователей"""
        self.stdout.write('Создаем ранги пользователей...')
        
        ranks_data = [
            {
                'name': 'Новичок',
                'required_points': 0,
                'icon_url': '/static/images/ranks/newbie.png'
            },
            {
                'name': 'Участник',
                'required_points': 100,
                'icon_url': '/static/images/ranks/member.png'
            },
            {
                'name': 'Активный участник',
                'required_points': 500,
                'icon_url': '/static/images/ranks/active-member.png'
            },
            {
                'name': 'Эксперт',
                'required_points': 1000,
                'icon_url': '/static/images/ranks/expert.png'
            },
            {
                'name': 'Гуру',
                'required_points': 2000,
                'icon_url': '/static/images/ranks/guru.png'
            }
        ]
        
        self.ranks = []
        for data in ranks_data:
            rank, created = UserRank.objects.get_or_create(
                name=data['name'],
                defaults={
                    'required_points': data['required_points'],
                    'icon_url': data['icon_url']
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Создан ранг: {rank.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'  Ранг уже существует: {rank.name}'))
            
            self.ranks.append(rank)
        
        # Назначаем ранги пользователям
        for user in self.users:
            try:
                rank_progress = UserRankProgress.objects.get(user=user)
                # Находим подходящий ранг
                suitable_rank = None
                for rank in reversed(self.ranks):  # От высшего к низшему
                    if rank_progress.current_points >= rank.required_points:
                        suitable_rank = rank
                        break
                
                if suitable_rank:
                    rank_progress.rank = suitable_rank
                    rank_progress.save()
            except UserRankProgress.DoesNotExist:
                pass
        
        self.stdout.write(self.style.SUCCESS(f'Создано {len(self.ranks)} рангов'))

    def assign_achievements(self):
        """Назначаем достижения пользователям"""
        self.stdout.write('Назначаем достижения пользователям...')
        
        achievements_assigned = 0
        
        for user in self.users:
            # Получаем количество сообщений пользователя
            post_count = Post.objects.filter(author=user, is_deleted=False).count()
            
            # Получаем количество тем пользователя
            topic_count = Topic.objects.filter(author=user).count()
            
            # Получаем количество лайков к сообщениям пользователя
            upvotes_count = PostLike.objects.filter(
                post__author=user,
                like_type='like'
            ).count()
            
            # Назначаем достижения на основе активности
            for achievement in self.achievements:
                criteria_type = achievement.criteria.get('type')
                criteria_value = achievement.criteria.get('value', 0)
                
                # Проверяем, удовлетворяет ли пользователь критериям
                should_assign = False
                if criteria_type == 'post_count' and post_count >= criteria_value:
                    should_assign = True
                elif criteria_type == 'topic_count' and topic_count >= criteria_value:
                    should_assign = True
                elif criteria_type == 'upvotes' and upvotes_count >= criteria_value:
                    should_assign = True
                elif 'course_id' in achievement.criteria:
                    # Для достижений по курсам назначаем случайным образом
                    should_assign = random.random() > 0.5
                
                # Назначаем достижение, если еще не назначено
                if should_assign:
                    user_achievement, created = UserAchievement.objects.get_or_create(
                        user=user,
                        achievement=achievement,
                        defaults={
                            'awarded_by': None
                        }
                    )
                    
                    if created:
                        achievements_assigned += 1
                        self.stdout.write(self.style.SUCCESS(f'  Назначено достижение "{achievement.name}" пользователю {user.username}'))
        
        self.stdout.write(self.style.SUCCESS(f'Назначено {achievements_assigned} достижений пользователям'))

    def assign_certificates(self):
        """Назначаем сертификаты пользователям"""
        self.stdout.write('Назначаем сертификаты пользователям...')
        
        certificates_assigned = 0
        
        for user in self.users:
            # Для демонстрации назначаем случайные сертификаты
            for certificate in self.certificates:
                # Назначаем сертификат с 60% вероятностью
                if random.random() > 0.4:
                    user_certificate, created = UserCertificate.objects.get_or_create(
                        user=user,
                        certificate=certificate,
                        defaults={
                            'awarded_by': None
                        }
                    )
                    
                    if created:
                        certificates_assigned += 1
                        self.stdout.write(self.style.SUCCESS(f'  Назначен сертификат "{certificate.name}" пользователю {user.username}'))
        
        self.stdout.write(self.style.SUCCESS(f'Назначено {certificates_assigned} сертификатов пользователям'))

    def create_likes_and_ratings(self):
        """Создаем лайки и оценки"""
        self.stdout.write('Создаем лайки и оценки...')
        
        likes_created = 0
        ratings_created = 0
        
        # Создаем лайки для сообщений
        for post in self.posts:
            # Количество лайков зависит от возраста сообщения
            days_since_creation = (timezone.now() - post.created_date).days
            max_likes = max(1, 20 - (days_since_creation // 2))  # Чем старше сообщение, тем меньше лайков
            
            # Создаем случайное количество лайков
            num_likes = random.randint(0, max_likes)
            
            for i in range(num_likes):
                # Выбираем случайного пользователя
                user = random.choice(self.users)
                
                # Проверяем, не поставил ли пользователь уже лайк
                existing_like = PostLike.objects.filter(post=post, user=user).first()
                if existing_like:
                    continue
                
                # Случайно выбираем лайк или дизлайк (80% лайков, 20% дизлайков)
                like_type = 'like' if random.random() > 0.2 else 'dislike'
                
                PostLike.objects.create(
                    post=post,
                    user=user,
                    like_type=like_type
                )
                
                likes_created += 1
        
        # Обновляем счетчики лайков в сообщениях
        for post in self.posts:
            post.like_count = PostLike.objects.filter(post=post, like_type='like').count()
            post.dislike_count = PostLike.objects.filter(post=post, like_type='dislike').count()
            post.save()
        
        # Создаем оценки для тем
        for topic in self.topics:
            # Количество оценок зависит от возраста темы
            days_since_creation = (timezone.now() - topic.created_date).days
            max_ratings = max(1, 15 - (days_since_creation // 3))
            
            # Создаем случайное количество оценок
            num_ratings = random.randint(0, max_ratings)
            
            for i in range(num_ratings):
                # Выбираем случайного пользователя
                user = random.choice(self.users)
                
                # Проверяем, не поставил ли пользователь уже оценку
                existing_rating = TopicRating.objects.filter(topic=topic, user=user).first()
                if existing_rating:
                    continue
                
                # Случайная оценка от 1 до 5
                rating_value = random.randint(1, 5)
                
                TopicRating.objects.create(
                    topic=topic,
                    user=user,
                    rating=rating_value
                )
                
                ratings_created += 1
        
        # Обновляем средние оценки в темах
        for topic in self.topics:
            ratings = TopicRating.objects.filter(topic=topic)
            if ratings.exists():
                topic.rating_count = ratings.count()
                topic.average_rating = sum(r.rating for r in ratings) / topic.rating_count
                topic.save()
        
        self.stdout.write(self.style.SUCCESS(f'Создано {likes_created} лайков и {ratings_created} оценок'))