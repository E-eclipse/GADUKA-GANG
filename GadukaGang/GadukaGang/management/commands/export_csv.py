"""
Django management команда для экспорта данных в CSV
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from GadukaGang.models import Section, Topic, Post, Tag, Achievement, UserRank, UserProfile
import csv
import os
from datetime import datetime

User = get_user_model()


class Command(BaseCommand):
    help = 'Экспортирует данные в CSV файлы'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            required=True,
            choices=['users', 'sections', 'topics', 'posts', 'tags', 'achievements', 'ranks', 'all'],
            help='Тип данных для экспорта'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='exports',
            help='Директория для сохранения файлов'
        )

    def handle(self, *args, **options):
        export_type = options['type']
        output_dir = options['output']
        
        # Создаём директорию если не существует
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        self.stdout.write(self.style.SUCCESS(f'\n📤 Экспорт данных'))
        self.stdout.write('=' * 60)
        
        if export_type == 'all':
            self.export_users(output_dir, timestamp)
            self.export_sections(output_dir, timestamp)
            self.export_topics(output_dir, timestamp)
            self.export_posts(output_dir, timestamp)
            self.export_tags(output_dir, timestamp)
            self.export_achievements(output_dir, timestamp)
            self.export_ranks(output_dir, timestamp)
        else:
            if export_type == 'users':
                self.export_users(output_dir, timestamp)
            elif export_type == 'sections':
                self.export_sections(output_dir, timestamp)
            elif export_type == 'topics':
                self.export_topics(output_dir, timestamp)
            elif export_type == 'posts':
                self.export_posts(output_dir, timestamp)
            elif export_type == 'tags':
                self.export_tags(output_dir, timestamp)
            elif export_type == 'achievements':
                self.export_achievements(output_dir, timestamp)
            elif export_type == 'ranks':
                self.export_ranks(output_dir, timestamp)
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Экспорт завершён'))

    def export_users(self, output_dir, timestamp):
        """Экспорт пользователей с полной статистикой"""
        filename = os.path.join(output_dir, f'users_{timestamp}.csv')
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Имя пользователя', 'Email', 'Имя', 'Фамилия', 'Роль', 'Статус',
                'Дата регистрации', 'Последняя активность', 'Количество постов', 
                'Количество тем', 'Достижений', 'Текущий ранг', 'Очки ранга'
            ])
            
            users = User.objects.select_related('userprofile').prefetch_related(
                'userachievement_set__achievement',
                'userrankprogress'
            ).all()
            
            for user in users:
                try:
                    profile = user.userprofile
                    post_count = profile.post_count
                    last_activity = profile.last_activity.strftime('%Y-%m-%d %H:%M') if profile.last_activity else 'Никогда'
                except:
                    post_count = 0
                    last_activity = 'Никогда'
                
                # Количество тем
                topics_count = Topic.objects.filter(author=user).count()
                
                # Достижения
                achievements_count = user.userachievement_set.count()
                
                # Ранг
                try:
                    rank_progress = user.userrankprogress
                    current_rank = rank_progress.current_rank.name if rank_progress.current_rank else 'Нет ранга'
                    rank_points = rank_progress.current_points
                except:
                    current_rank = 'Нет ранга'
                    rank_points = 0
                
                writer.writerow([
                    user.username,
                    user.email,
                    user.first_name or '',
                    user.last_name or '',
                    user.get_role_display(),
                    'Активен' if user.is_active else 'Заблокирован',
                    user.registration_date.strftime('%Y-%m-%d %H:%M:%S') if user.registration_date else '',
                    last_activity,
                    post_count,
                    topics_count,
                    achievements_count,
                    current_rank,
                    rank_points
                ])
        
        count = User.objects.count()
        self.stdout.write(f'  ✓ Пользователи: {count} → {filename}')

    def export_sections(self, output_dir, timestamp):
        """Экспорт разделов с полной статистикой"""
        filename = os.path.join(output_dir, f'sections_{timestamp}.csv')
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Название раздела', 'Описание', 'Создатель', 'Email создателя',
                'Дата создания', 'Количество тем', 'Количество постов', 
                'Уникальных авторов', 'Последняя активность'
            ])
            
            sections = Section.objects.select_related('created_by').prefetch_related('topic_set__post_set').all()
            for section in sections:
                topics = section.topic_set.all()
                topics_count = topics.count()
                posts_count = sum(t.post_set.filter(is_deleted=False).count() for t in topics)
                
                # Уникальные авторы
                unique_authors = set()
                for topic in topics:
                    unique_authors.add(topic.author_id)
                    for post in topic.post_set.filter(is_deleted=False):
                        unique_authors.add(post.author_id)
                
                # Последняя активность
                last_post = Post.objects.filter(
                    topic__section=section, 
                    is_deleted=False
                ).order_by('-created_date').first()
                last_activity = last_post.created_date.strftime('%Y-%m-%d %H:%M') if last_post else 'Нет активности'
                
                writer.writerow([
                    section.name,
                    section.description[:200] if section.description else '',
                    section.created_by.username if section.created_by else 'Система',
                    section.created_by.email if section.created_by else '',
                    section.created_date.strftime('%Y-%m-%d %H:%M:%S') if section.created_date else '',
                    topics_count,
                    posts_count,
                    len(unique_authors),
                    last_activity
                ])
        
        count = Section.objects.count()
        self.stdout.write(f'  ✓ Разделы: {count} → {filename}')

    def export_topics(self, output_dir, timestamp):
        """Экспорт тем с полными данными"""
        filename = os.path.join(output_dir, f'topics_{timestamp}.csv')
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                'ID темы', 'Название', 'Раздел', 'Автор', 'Email автора', 'Роль автора',
                'Дата создания', 'Закреплена', 'Просмотров', 'Средний рейтинг', 
                'Количество постов', 'Теги', 'Последний пост'
            ])
            
            topics = Topic.objects.select_related('section', 'author').prefetch_related('tags', 'post_set').all()
            for topic in topics:
                # Собираем теги
                tags = ', '.join([tag.name for tag in topic.tags.all()]) if topic.tags.exists() else 'Нет тегов'
                
                # Получаем дату последнего поста
                last_post = topic.post_set.filter(is_deleted=False).order_by('-created_date').first()
                last_post_date = last_post.created_date.strftime('%Y-%m-%d %H:%M') if last_post else 'Нет постов'
                
                writer.writerow([
                    topic.id,
                    topic.title,
                    topic.section.name,
                    topic.author.username,
                    topic.author.email,
                    topic.author.get_role_display(),
                    topic.created_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'Да' if topic.is_pinned else 'Нет',
                    topic.view_count,
                    round(topic.average_rating, 2),
                    topic.post_set.filter(is_deleted=False).count(),
                    tags,
                    last_post_date
                ])
        
        count = Topic.objects.count()
        self.stdout.write(f'  ✓ Темы: {count} → {filename}')

    def export_posts(self, output_dir, timestamp):
        """Экспорт постов с полными данными"""
        filename = os.path.join(output_dir, f'posts_{timestamp}.csv')
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                'ID поста', 'Тема', 'Раздел', 'Автор', 'Email автора', 'Роль автора',
                'Содержимое', 'Дата создания', 'Отредактирован', 'Удалён', 
                'Лайков', 'Дизлайков', 'Рейтинг', 'Номер редакции'
            ])
            
            posts = Post.objects.select_related('topic__section', 'author').all()[:10000]
            for post in posts:
                # Вычисляем рейтинг
                rating = post.like_count - post.dislike_count
                
                writer.writerow([
                    post.id,
                    post.topic.title,
                    post.topic.section.name,
                    post.author.username,
                    post.author.email,
                    post.author.get_role_display(),
                    post.content[:1000],  # Ограничиваем до 1000 символов
                    post.created_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'Да' if post.edit_count > 0 else 'Нет',
                    'Да' if post.is_deleted else 'Нет',
                    post.like_count,
                    post.dislike_count,
                    f'+{rating}' if rating > 0 else str(rating),
                    post.edit_count
                ])
        
        count = min(Post.objects.count(), 10000)
        self.stdout.write(f'  ✓ Посты: {count} → {filename}')

    def export_tags(self, output_dir, timestamp):
        """Экспорт тегов с статистикой использования"""
        filename = os.path.join(output_dir, f'tags_{timestamp}.csv')
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Название тега', 'Цвет', 'Количество тем', 'Уникальных авторов',
                'Общих просмотров', 'Средний рейтинг тем', 'Популярность'
            ])
            
            tags = Tag.objects.prefetch_related('topic_set__author').all()
            for tag in tags:
                topics = tag.topic_set.all()
                topics_count = topics.count()
                
                if topics_count > 0:
                    # Уникальные авторы
                    unique_authors = set(t.author_id for t in topics)
                    
                    # Общие просмотры
                    total_views = sum(t.view_count for t in topics)
                    
                    # Средний рейтинг
                    avg_rating = sum(t.average_rating for t in topics) / topics_count
                    
                    # Популярность (на основе просмотров и тем)
                    popularity = 'Высокая' if total_views > 1000 or topics_count > 20 else \
                                'Средняя' if total_views > 100 or topics_count > 5 else 'Низкая'
                else:
                    unique_authors = set()
                    total_views = 0
                    avg_rating = 0
                    popularity = 'Не используется'
                
                writer.writerow([
                    tag.name,
                    tag.color,
                    topics_count,
                    len(unique_authors),
                    total_views,
                    round(avg_rating, 2),
                    popularity
                ])
        
        count = Tag.objects.count()
        self.stdout.write(f'  ✓ Теги: {count} → {filename}')

    def export_achievements(self, output_dir, timestamp):
        """Экспорт достижений"""
        filename = os.path.join(output_dir, f'achievements_{timestamp}.csv')
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'description', 'icon_url', 'criteria'])
            
            achievements = Achievement.objects.all()
            for achievement in achievements:
                import json
                writer.writerow([
                    achievement.name,
                    achievement.description,
                    achievement.icon_url,
                    json.dumps(achievement.criteria, ensure_ascii=False)
                ])
        
        count = Achievement.objects.count()
        self.stdout.write(f'  ✓ Достижения: {count} → {filename}')

    def export_ranks(self, output_dir, timestamp):
        """Экспорт рангов"""
        filename = os.path.join(output_dir, f'ranks_{timestamp}.csv')
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'required_points', 'icon_url'])
            
            ranks = UserRank.objects.all().order_by('required_points')
            for rank in ranks:
                writer.writerow([
                    rank.name,
                    rank.required_points,
                    rank.icon_url
                ])
        
        count = UserRank.objects.count()
        self.stdout.write(f'  ✓ Ранги: {count} → {filename}')
