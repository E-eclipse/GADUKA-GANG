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
    Course, Lesson, CourseProgress
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Создает курсы и наполняет аналитику данными без удаления существующих данных'

    def handle(self, *args, **options):
        self.stdout.write('Начинаем создание курсов и наполнение аналитики...')
        
        # Создаем курсы
        self.create_courses()
        
        # Наполняем аналитику данными
        self.populate_analytics()
        
        self.stdout.write(self.style.SUCCESS('Курсы созданы и аналитика наполнена!'))

    def create_courses(self):
        """Создаем курсы обучения"""
        self.stdout.write('Создаем курсы...')
        
        # Создаем курс "Python для начинающих"
        course1, created1 = Course.objects.get_or_create(
            title='Python для начинающих',
            defaults={
                'description': 'Подробный курс по основам Python. Изучите переменные, типы данных, циклы и многое другое.',
                'order': 1,
                'is_active': True
            }
        )
        
        if created1:
            self.stdout.write(self.style.SUCCESS(f'  Создан курс: {course1.title}'))
        else:
            self.stdout.write(self.style.WARNING(f'  Курс уже существует: {course1.title}'))
            # Удаляем старые уроки для пересоздания
            course1.lessons.all().delete()
        
        # Создаем уроки для курса "Python для начинающих"
        lessons_data_1 = [
            {
                'title': 'Введение в Python',
                'content': '''# Введение в Python

Python — это высокоуровневый язык программирования, который известен своей простотой и читаемостью.

## Что такое Python?

Python был создан Гвидо ван Россумом и впервые выпущен в 1991 году. Название языка происходит от комедийного шоу "Monty Python's Flying Circus".

## Преимущества Python:

- **Простота**: Синтаксис Python очень понятный и похож на обычный английский язык
- **Универсальность**: Python используется для веб-разработки, анализа данных, машинного обучения и многого другого
- **Большое сообщество**: Множество библиотек и активное сообщество разработчиков

## Ваша первая программа

Давайте начнем с классической программы "Hello, World!":

```python
print("Hello, World!")
```

Эта программа выводит текст "Hello, World!" на экран. Функция `print()` используется для вывода данных.''',
                'lesson_type': 'lecture',
                'order': 1
            },
            {
                'title': 'Переменные',
                'content': '''# Переменные в Python

Переменная — это именованная область памяти, где хранятся данные.

## Создание переменных

В Python переменные создаются простым присваиванием значения:

```python
name = "Иван"
age = 25
height = 1.75
```

## Правила именования переменных:

- Имя должно начинаться с буквы или подчеркивания
- Может содержать буквы, цифры и подчеркивания
- Регистр имеет значение (name и Name — разные переменные)
- Нельзя использовать зарезервированные слова (if, for, class и т.д.)

## Примеры:

```python
# Строка
name = "Python"

# Число
number = 42

# Дробное число
pi = 3.14

# Булево значение
is_active = True
```''',
                'lesson_type': 'lecture',
                'order': 2
            },
            {
                'title': 'Практика: Работа с переменными',
                'content': '''# Практическое задание: Переменные

Создайте переменные для хранения информации о себе:
- Ваше имя
- Ваш возраст
- Ваш любимый язык программирования

Затем выведите эту информацию на экран.''',
                'lesson_type': 'practice',
                'order': 3,
                'practice_code_template': '# Создайте переменные здесь\nname = ""\nage = 0\nfavorite_language = ""\n\n# Выведите информацию\nprint("Имя:", name)\nprint("Возраст:", age)\nprint("Любимый язык:", favorite_language)',
                'test_cases': [
                    {'input': '', 'output': 'Имя: \nВозраст: 0\nЛюбимый язык: '}
                ]
            }
        ]
        
        # Создаем уроки для первого курса
        for lesson_data in lessons_data_1:
            lesson, created = Lesson.objects.get_or_create(
                course=course1,
                title=lesson_data['title'],
                defaults={
                    'content': lesson_data['content'],
                    'lesson_type': lesson_data['lesson_type'],
                    'order': lesson_data['order'],
                    'practice_code_template': lesson_data.get('practice_code_template', ''),
                    'test_cases': lesson_data.get('test_cases', []),
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'    Создан урок: {lesson.title}'))
            else:
                self.stdout.write(self.style.WARNING(f'    Урок уже существует: {lesson.title}'))
        
        # Создаем курс "Python для продвинутых"
        course2, created2 = Course.objects.get_or_create(
            title='Python для продвинутых',
            defaults={
                'description': 'Продвинутый курс по Python. Работа с алгоритмами, структурами данных и сложными задачами.',
                'order': 2,
                'is_active': True
            }
        )
        
        if created2:
            self.stdout.write(self.style.SUCCESS(f'  Создан курс: {course2.title}'))
        else:
            self.stdout.write(self.style.WARNING(f'  Курс уже существует: {course2.title}'))
            # Удаляем старые уроки для пересоздания
            course2.lessons.all().delete()
        
        # Создаем уроки для курса "Python для продвинутых"
        lessons_data_2 = [
            {
                'title': 'Работа со списками и алгоритмы',
                'content': '''# Работа со списками и алгоритмы

В этом уроке мы изучим продвинутые техники работы со списками и базовые алгоритмы.

## Методы списков

```python
numbers = [1, 2, 3, 4, 5]
numbers.append(6)  # Добавить элемент
numbers.extend([7, 8])  # Расширить список
numbers.insert(0, 0)  # Вставить элемент
numbers.remove(3)  # Удалить элемент
numbers.pop()  # Удалить последний элемент
```

## Сортировка

```python
numbers = [3, 1, 4, 1, 5, 9, 2, 6]
numbers.sort()  # Сортировка на месте
sorted_numbers = sorted(numbers)  # Возвращает новый список
```

## Поиск и фильтрация

```python
numbers = [1, 2, 3, 4, 5]
index = numbers.index(3)  # Найти индекс элемента
filtered = [x for x in numbers if x > 3]  # Списочное включение
```''',
                'lesson_type': 'lecture',
                'order': 1
            },
            {
                'title': 'Практика: Сортировка и поиск',
                'content': '''# Практическое задание: Сортировка и поиск

Напишите программу, которая:
1. Принимает список чисел через input (числа разделены пробелами)
2. Сортирует список по убыванию
3. Выводит отсортированный список, каждое число на новой строке

**Пример входных данных:**
```
5 2 8 1 9 3
```

**Ожидаемый вывод:**
```
9
8
5
3
2
1
```''',
                'lesson_type': 'practice',
                'order': 2,
                'practice_code_template': '# Введите код здесь\n# Используйте input() для получения данных\n# Числа разделены пробелами\n',
                'test_cases': [
                    {'input': '5 2 8 1 9 3', 'output': '9\n8\n5\n3\n2\n1'},
                    {'input': '1 2 3', 'output': '3\n2\n1'}
                ]
            }
        ]
        
        # Создаем уроки для второго курса
        for lesson_data in lessons_data_2:
            lesson, created = Lesson.objects.get_or_create(
                course=course2,
                title=lesson_data['title'],
                defaults={
                    'content': lesson_data['content'],
                    'lesson_type': lesson_data['lesson_type'],
                    'order': lesson_data['order'],
                    'practice_code_template': lesson_data.get('practice_code_template', ''),
                    'test_cases': lesson_data.get('test_cases', []),
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'    Создан урок: {lesson.title}'))
            else:
                self.stdout.write(self.style.WARNING(f'    Урок уже существует: {lesson.title}'))
        
        self.stdout.write(self.style.SUCCESS(f'Создано 2 курса с уроками'))

    def populate_analytics(self):
        """Наполняем аналитику данными"""
        self.stdout.write('Наполняем аналитику данными...')
        
        # Получаем всех пользователей
        users = list(User.objects.all())
        if not users:
            self.stdout.write(self.style.WARNING('  Нет пользователей для создания аналитики'))
            return
        
        # Получаем все темы
        topics = list(Topic.objects.all())
        if not topics:
            self.stdout.write(self.style.WARNING('  Нет тем для создания аналитики'))
            return
        
        # Получаем все сообщения
        posts = list(Post.objects.all())
        if not posts:
            self.stdout.write(self.style.WARNING('  Нет сообщений для создания аналитики'))
            return
        
        # Создаем просмотры тем (для аналитики)
        views_created = 0
        from GadukaGang.models import TopicView
        for topic in topics[:20]:  # Ограничиваем для производительности
            # Создаем просмотры для случайных пользователей
            viewers = random.sample(users, min(len(users), random.randint(1, 5)))
            for user in viewers:
                # Создаем просмотры с разными датами
                days_ago = random.randint(0, 30)
                view_date = timezone.now() - timedelta(days=days_ago)
                
                TopicView.objects.get_or_create(
                    topic=topic,
                    user=user,
                    defaults={
                        'view_date': view_date
                    }
                )
                views_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'  Создано просмотров тем: {views_created}'))
        
        # Создаем лайки для сообщений (для аналитики)
        likes_created = 0
        for post in posts[:50]:  # Ограничиваем для производительности
            # Создаем лайки от случайных пользователей
            likers = random.sample(users, min(len(users), random.randint(0, 3)))
            for user in likers:
                # Проверяем, не поставил ли пользователь уже лайк
                existing_like = PostLike.objects.filter(post=post, user=user).first()
                if existing_like:
                    continue
                
                # Случайно выбираем лайк или дизлайк
                like_type = 'like' if random.random() > 0.2 else 'dislike'
                
                PostLike.objects.create(
                    post=post,
                    user=user,
                    like_type=like_type
                )
                likes_created += 1
        
        # Обновляем счетчики лайков в сообщениях
        for post in posts:
            post.like_count = PostLike.objects.filter(post=post, like_type='like').count()
            post.dislike_count = PostLike.objects.filter(post=post, like_type='dislike').count()
            post.save()
        
        self.stdout.write(self.style.SUCCESS(f'  Создано лайков/дизлайков: {likes_created}'))
        
        # Создаем оценки для тем (для аналитики)
        ratings_created = 0
        for topic in topics[:30]:  # Ограничиваем для производительности
            # Создаем оценки от случайных пользователей
            raters = random.sample(users, min(len(users), random.randint(0, 5)))
            for user in raters:
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
        for topic in topics:
            ratings = TopicRating.objects.filter(topic=topic)
            if ratings.exists():
                topic.rating_count = ratings.count()
                topic.average_rating = sum(r.rating for r in ratings) / topic.rating_count
                topic.save()
        
        self.stdout.write(self.style.SUCCESS(f'  Создано оценок тем: {ratings_created}'))
        
        # Обновляем счетчики сообщений в профилях пользователей
        for user in users:
            try:
                profile = user.userprofile
                post_count = Post.objects.filter(author=user, is_deleted=False).count()
                profile.post_count = post_count
                profile.save(update_fields=['post_count'])
            except UserProfile.DoesNotExist:
                pass
        
        self.stdout.write(self.style.SUCCESS('  Обновлены профили пользователей'))
        
        # Создаем прогресс курсов для пользователей
        courses = list(Course.objects.all())
        progress_created = 0
        for user in users:
            for course in courses:
                # С вероятностью 30% создаем прогресс курса
                if random.random() > 0.7:
                    progress, created = CourseProgress.objects.get_or_create(
                        user=user,
                        course=course,
                        defaults={
                            'started_date': timezone.now() - timedelta(days=random.randint(1, 30))
                        }
                    )
                    
                    if created:
                        # С вероятностью 50% отмечаем некоторые уроки как завершенные
                        lessons = list(course.lessons.all())
                        completed_lessons = random.sample(lessons, min(len(lessons), random.randint(0, len(lessons))))
                        progress.completed_lessons.set(completed_lessons)
                        
                        # Если все уроки завершены, отмечаем курс как завершенный
                        if len(completed_lessons) == len(lessons):
                            progress.is_completed = True
                            progress.completed_date = timezone.now() - timedelta(days=random.randint(0, 10))
                            progress.save()
                        
                        progress_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'  Создано прогрессов курсов: {progress_created}'))
        
        self.stdout.write(self.style.SUCCESS('Аналитика успешно наполнена'))