"""
Django management команда для импорта данных из CSV
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from GadukaGang.models import Section, Topic, Post, Tag, Achievement, UserRank
import csv
import os
from datetime import datetime

User = get_user_model()


class Command(BaseCommand):
    help = 'Импортирует данные из CSV файлов с валидацией'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            required=True,
            choices=['users', 'sections', 'topics', 'posts', 'tags', 'achievements', 'ranks'],
            help='Тип данных для импорта'
        )
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Путь к CSV файлу'
        )
        parser.add_argument(
            '--skip-errors',
            action='store_true',
            help='Пропускать строки с ошибками'
        )

    def handle(self, *args, **options):
        import_type = options['type']
        file_path = options['file']
        skip_errors = options.get('skip_errors', False)
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'Файл не найден: {file_path}'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\n📥 Импорт {import_type} из {file_path}'))
        self.stdout.write('=' * 60)
        
        try:
            if import_type == 'users':
                self.import_users(file_path, skip_errors)
            elif import_type == 'sections':
                self.import_sections(file_path, skip_errors)
            elif import_type == 'topics':
                self.import_topics(file_path, skip_errors)
            elif import_type == 'posts':
                self.import_posts(file_path, skip_errors)
            elif import_type == 'tags':
                self.import_tags(file_path, skip_errors)
            elif import_type == 'achievements':
                self.import_achievements(file_path, skip_errors)
            elif import_type == 'ranks':
                self.import_ranks(file_path, skip_errors)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Ошибка импорта: {e}'))
            raise

    def import_users(self, file_path, skip_errors):
        """Импорт пользователей"""
        success_count = 0
        error_count = 0
        
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    with transaction.atomic():
                        # Валидация обязательных полей
                        if not row.get('username'):
                            raise ValueError('Отсутствует username')
                        if not row.get('email'):
                            raise ValueError('Отсутствует email')
                        
                        # Проверка на дубликаты
                        if User.objects.filter(username=row['username']).exists():
                            raise ValueError(f'Пользователь {row["username"]} уже существует')
                        
                        # Создание пользователя
                        user = User.objects.create_user(
                            username=row['username'],
                            email=row['email'],
                            password=row.get('password', 'defaultpass123'),
                            first_name=row.get('first_name', ''),
                            last_name=row.get('last_name', ''),
                            is_active=row.get('is_active', 'True').lower() == 'true',
                        )
                        
                        # Установка роли
                        if row.get('role'):
                            user.role = row['role']
                            user.save()
                        
                        success_count += 1
                        self.stdout.write(f'  ✓ Строка {row_num}: {user.username}')
                
                except Exception as e:
                    error_count += 1
                    if skip_errors:
                        self.stdout.write(self.style.WARNING(f'  ⚠ Строка {row_num}: {e}'))
                    else:
                        raise Exception(f'Ошибка в строке {row_num}: {e}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Импортировано: {success_count}'))
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'⚠ Ошибок: {error_count}'))

    def import_sections(self, file_path, skip_errors):
        """Импорт разделов форума"""
        success_count = 0
        error_count = 0
        
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    with transaction.atomic():
                        if not row.get('name'):
                            raise ValueError('Отсутствует название раздела')
                        
                        # Поиск создателя
                        created_by = None
                        if row.get('created_by'):
                            created_by = User.objects.filter(username=row['created_by']).first()
                        
                        section, created = Section.objects.get_or_create(
                            name=row['name'],
                            defaults={
                                'description': row.get('description', ''),
                                'created_by': created_by
                            }
                        )
                        
                        success_count += 1
                        status = 'создан' if created else 'обновлён'
                        self.stdout.write(f'  ✓ Строка {row_num}: {section.name} ({status})')
                
                except Exception as e:
                    error_count += 1
                    if skip_errors:
                        self.stdout.write(self.style.WARNING(f'  ⚠ Строка {row_num}: {e}'))
                    else:
                        raise Exception(f'Ошибка в строке {row_num}: {e}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Импортировано: {success_count}'))
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'⚠ Ошибок: {error_count}'))

    def import_topics(self, file_path, skip_errors):
        """Импорт тем"""
        success_count = 0
        error_count = 0
        
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    with transaction.atomic():
                        if not row.get('title'):
                            raise ValueError('Отсутствует название темы')
                        if not row.get('section'):
                            raise ValueError('Отсутствует раздел')
                        if not row.get('author'):
                            raise ValueError('Отсутствует автор')
                        
                        # Поиск раздела и автора
                        section = Section.objects.filter(name=row['section']).first()
                        if not section:
                            raise ValueError(f'Раздел "{row["section"]}" не найден')
                        
                        author = User.objects.filter(username=row['author']).first()
                        if not author:
                            raise ValueError(f'Автор "{row["author"]}" не найден')
                        
                        topic = Topic.objects.create(
                            section=section,
                            title=row['title'],
                            author=author,
                            is_pinned=row.get('is_pinned', 'False').lower() == 'true'
                        )
                        
                        success_count += 1
                        self.stdout.write(f'  ✓ Строка {row_num}: {topic.title}')
                
                except Exception as e:
                    error_count += 1
                    if skip_errors:
                        self.stdout.write(self.style.WARNING(f'  ⚠ Строка {row_num}: {e}'))
                    else:
                        raise Exception(f'Ошибка в строке {row_num}: {e}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Импортировано: {success_count}'))
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'⚠ Ошибок: {error_count}'))

    def import_posts(self, file_path, skip_errors):
        """Импорт постов"""
        success_count = 0
        error_count = 0
        
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    with transaction.atomic():
                        if not row.get('topic_id'):
                            raise ValueError('Отсутствует ID темы')
                        if not row.get('author'):
                            raise ValueError('Отсутствует автор')
                        if not row.get('content'):
                            raise ValueError('Отсутствует содержимое')
                        
                        topic = Topic.objects.filter(id=row['topic_id']).first()
                        if not topic:
                            raise ValueError(f'Тема #{row["topic_id"]} не найдена')
                        
                        author = User.objects.filter(username=row['author']).first()
                        if not author:
                            raise ValueError(f'Автор "{row["author"]}" не найден')
                        
                        post = Post.objects.create(
                            topic=topic,
                            author=author,
                            content=row['content']
                        )
                        
                        success_count += 1
                        self.stdout.write(f'  ✓ Строка {row_num}: Пост #{post.id}')
                
                except Exception as e:
                    error_count += 1
                    if skip_errors:
                        self.stdout.write(self.style.WARNING(f'  ⚠ Строка {row_num}: {e}'))
                    else:
                        raise Exception(f'Ошибка в строке {row_num}: {e}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Импортировано: {success_count}'))
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'⚠ Ошибок: {error_count}'))

    def import_tags(self, file_path, skip_errors):
        """Импорт тегов"""
        success_count = 0
        error_count = 0
        
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    with transaction.atomic():
                        if not row.get('name'):
                            raise ValueError('Отсутствует название тега')
                        
                        tag, created = Tag.objects.get_or_create(
                            name=row['name'],
                            defaults={'color': row.get('color', '#00FF41')}
                        )
                        
                        success_count += 1
                        status = 'создан' if created else 'существует'
                        self.stdout.write(f'  ✓ Строка {row_num}: {tag.name} ({status})')
                
                except Exception as e:
                    error_count += 1
                    if skip_errors:
                        self.stdout.write(self.style.WARNING(f'  ⚠ Строка {row_num}: {e}'))
                    else:
                        raise Exception(f'Ошибка в строке {row_num}: {e}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Импортировано: {success_count}'))
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'⚠ Ошибок: {error_count}'))

    def import_achievements(self, file_path, skip_errors):
        """Импорт достижений"""
        success_count = 0
        error_count = 0
        
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    with transaction.atomic():
                        if not row.get('name'):
                            raise ValueError('Отсутствует название достижения')
                        
                        # Парсим criteria из JSON-строки
                        import json
                        criteria = json.loads(row.get('criteria', '{}'))
                        
                        achievement, created = Achievement.objects.get_or_create(
                            name=row['name'],
                            defaults={
                                'description': row.get('description', ''),
                                'icon_url': row.get('icon_url', ''),
                                'criteria': criteria
                            }
                        )
                        
                        success_count += 1
                        status = 'создано' if created else 'существует'
                        self.stdout.write(f'  ✓ Строка {row_num}: {achievement.name} ({status})')
                
                except Exception as e:
                    error_count += 1
                    if skip_errors:
                        self.stdout.write(self.style.WARNING(f'  ⚠ Строка {row_num}: {e}'))
                    else:
                        raise Exception(f'Ошибка в строке {row_num}: {e}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Импортировано: {success_count}'))
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'⚠ Ошибок: {error_count}'))

    def import_ranks(self, file_path, skip_errors):
        """Импорт рангов"""
        success_count = 0
        error_count = 0
        
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    with transaction.atomic():
                        if not row.get('name'):
                            raise ValueError('Отсутствует название ранга')
                        if not row.get('required_points'):
                            raise ValueError('Отсутствует required_points')
                        
                        rank, created = UserRank.objects.get_or_create(
                            name=row['name'],
                            defaults={
                                'required_points': int(row['required_points']),
                                'icon_url': row.get('icon_url', '')
                            }
                        )
                        
                        success_count += 1
                        status = 'создан' if created else 'существует'
                        self.stdout.write(f'  ✓ Строка {row_num}: {rank.name} ({status})')
                
                except Exception as e:
                    error_count += 1
                    if skip_errors:
                        self.stdout.write(self.style.WARNING(f'  ⚠ Строка {row_num}: {e}'))
                    else:
                        raise Exception(f'Ошибка в строке {row_num}: {e}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Импортировано: {success_count}'))
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'⚠ Ошибок: {error_count}'))
