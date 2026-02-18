from django.core.management.base import BaseCommand
from GadukaGang.models import Course, Lesson

class Command(BaseCommand):
    help = 'Создает курс Web Development с Django с лекциями и практическими заданиями'

    def handle(self, *args, **options):
        # Создать или получить курс Django
        course, created = Course.objects.get_or_create(
            title='Web Development с Django',
            defaults={
                'description': 'Полный курс по веб-разработке с использованием Django. Создание веб-приложений, работа с базами данных, аутентификация и многое другое.',
                'order': 4,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Создан курс: {course.title}'))
        else:
            self.stdout.write(self.style.WARNING(f'Курс уже существует: {course.title}'))
            # Удалить старые уроки для пересоздания
            course.lessons.all().delete()
        
        # Определить уроки
        lessons_data = [
            {
                'title': 'Введение в Django',
                'content': '''# Введение в Django

Django — это высокоуровневый фреймворк для веб-разработки на Python, который позволяет быстро создавать безопасные и поддерживаемые веб-сайты.

## Что такое Django?

Django был создан в 2003 году в газете Lawrence Journal-World. Название происходит от джазового гитариста Django Reinhardt.

## Преимущества Django:

- **Быстрая разработка**: Django помогает разрабатывать приложения быстрее
- **Безопасность**: Встроенные средства защиты от распространенных уязвимостей
- **Масштабируемость**: Подходит для проектов любого размера
- **ORM**: Объектно-реляционное отображение для работы с базами данных

## Архитектура MTV

Django использует архитектуру Model-Template-View:
- **Model** — данные и бизнес-логика
- **Template** — представление (HTML)
- **View** — логика обработки запросов

## Ваше первое приложение

Для создания проекта используйте команду:
```bash
django-admin startproject myproject
```

Для запуска сервера:
```bash
python manage.py runserver
```''',
                'lesson_type': 'lecture',
                'order': 1
            },
            {
                'title': 'Практика: Создание первого проекта Django',
                'content': '''# Практическое задание: Создание первого проекта Django

Создайте простое Django-приложение:

1. Создайте новый проект Django с именем "my_first_site"
2. Запустите сервер разработки
3. Откройте сайт в браузере и убедитесь, что он работает
4. Измените заголовок страницы на "Мой первый сайт на Django"

**Подсказки:**
- Используйте команду `django-admin startproject`
- Для запуска сервера используйте `python manage.py runserver`
- Главная страница находится в файле `templates/admin/base_site.html` или создайте свой шаблон''',
                'lesson_type': 'practice',
                'order': 2,
                'practice_code_template': '# Создайте проект Django и запустите сервер\n# Используйте команды в терминале:\n# django-admin startproject my_first_site\n# cd my_first_site\n# python manage.py runserver'
            },
            {
                'title': 'Модели в Django',
                'content': '''# Модели в Django

Модели в Django — это Python-классы, которые определяют структуру данных вашего приложения.

## Создание модели

```python
from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title
```

## Типы полей

- `CharField` — текстовое поле фиксированной длины
- `TextField` — большое текстовое поле
- `IntegerField` — целое число
- `DateTimeField` — дата и время
- `BooleanField` — логическое значение
- `ForeignKey` — связь с другой моделью

## Миграции

После создания модели нужно создать и применить миграции:
```bash
python manage.py makemigrations
python manage.py migrate
```''',
                'lesson_type': 'lecture',
                'order': 3
            },
            {
                'title': 'Практика: Создание моделей',
                'content': '''# Практическое задание: Создание моделей

Создайте модели для блога:

1. Модель `Post` с полями:
   - title (CharField, max_length=200)
   - content (TextField)
   - author (CharField, max_length=100)
   - created_date (DateTimeField, auto_now_add=True)
   - is_published (BooleanField, default=False)

2. Модель `Category` с полями:
   - name (CharField, max_length=100)
   - description (TextField, blank=True)

3. Добавьте связь между Post и Category (ForeignKey)

4. Создайте и примените миграции

**Подсказки:**
- Не забудьте импортировать models
- Используйте `python manage.py makemigrations` и `python manage.py migrate`''',
                'lesson_type': 'practice',
                'order': 4,
                'practice_code_template': '# Создайте модели Post и Category\nfrom django.db import models\n\n# Ваш код здесь\n\nclass Category(models.Model):\n    # Поля категории\n    pass\n\nclass Post(models.Model):\n    # Поля поста\n    # Не забудьте ForeignKey на Category\n    pass'
            },
            {
                'title': 'Views и URLs',
                'content': '''# Views и URLs в Django

Views обрабатывают HTTP-запросы и возвращают HTTP-ответы.

## Простая view-функция

```python
from django.http import HttpResponse

def hello(request):
    return HttpResponse("Привет, мир!")
```

## View с использованием шаблона

```python
from django.shortcuts import render

def home(request):
    context = {'name': 'Иван'}
    return render(request, 'home.html', context)
```

## URLs

В файле `urls.py`:

```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('hello/', views.hello, name='hello'),
]
```

## Передача параметров

```python
# urls.py
path('post/<int:post_id>/', views.post_detail, name='post_detail'),

# views.py
def post_detail(request, post_id):
    # post_id доступен как переменная
    return HttpResponse(f"Пост #{post_id}")
```''',
                'lesson_type': 'lecture',
                'order': 5
            },
            {
                'title': 'Практика: Создание Views',
                'content': '''# Практическое задание: Создание Views

Создайте views для блога:

1. Создайте view `post_list`, которая возвращает список всех опубликованных постов
2. Создайте view `post_detail`, которая показывает детали конкретного поста
3. Создайте view `category_posts`, которая показывает посты определенной категории
4. Настройте URLs для всех views

**Подсказки:**
- Используйте `render()` для возврата шаблонов
- Для получения данных из базы используйте `Post.objects.all()` или `Post.objects.filter()`
- Для передачи параметров в URL используйте `<int:id>` или `<str:slug>`''',
                'lesson_type': 'practice',
                'order': 6,
                'practice_code_template': '# Создайте views для блога\nfrom django.shortcuts import render, get_object_or_404\nfrom .models import Post, Category\n\n# Ваш код здесь\n\ndef post_list(request):\n    # Получите все опубликованные посты\n    pass\n\ndef post_detail(request, post_id):\n    # Получите пост по ID\n    pass\n\ndef category_posts(request, category_id):\n    # Получите посты категории\n    pass'
            },
            {
                'title': 'Шаблоны (Templates)',
                'content': '''# Шаблоны в Django

Шаблоны в Django используют язык шаблонов Django (DTL) для создания HTML.

## Базовый синтаксис

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
</head>
<body>
    <h1>{{ heading }}</h1>
    <p>{{ content }}</p>
</body>
</html>
```

## Циклы

```html
<ul>
{% for post in posts %}
    <li>{{ post.title }}</li>
{% endfor %}
</ul>
```

## Условия

```html
{% if user.is_authenticated %}
    <p>Привет, {{ user.username }}!</p>
{% else %}
    <p><a href="/login/">Войдите</a></p>
{% endif %}
```

## Наследование шаблонов

base.html:
```html
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}{% endblock %}</title>
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>
```

child.html:
```html
{% extends "base.html" %}

{% block title %}Мой сайт{% endblock %}

{% block content %}
    <h1>Добро пожаловать!</h1>
{% endblock %}
```''',
                'lesson_type': 'lecture',
                'order': 7
            },
            {
                'title': 'Практика: Создание шаблонов',
                'content': '''# Практическое задание: Создание шаблонов

Создайте шаблоны для блога:

1. Создайте базовый шаблон `base.html` с навигацией
2. Создайте шаблон `post_list.html` для отображения списка постов
3. Создайте шаблон `post_detail.html` для отображения деталей поста
4. Создайте шаблон `category_posts.html` для отображения постов категории

**Требования:**
- Используйте наследование шаблонов
- Добавьте навигацию между страницами
- Отобразите данные постов в цикле
- Добавьте условие для отображения статуса публикации''',
                'lesson_type': 'practice',
                'order': 8,
                'practice_code_template': '<!-- base.html -->\n<!DOCTYPE html>\n<html>\n<head>\n    <title>{% block title %}Мой блог{% endblock %}</title>\n</head>\n<body>\n    <nav>\n        <!-- Навигация -->\n    </nav>\n    \n    <main>\n        {% block content %}\n        {% endblock %}\n    </main>\n</body>\n</html>\n\n<!-- post_list.html -->\n{% extends "base.html" %}\n\n{% block content %}\n    <!-- Список постов -->\n{% endblock %}'
            },
            {
                'title': 'Формы в Django',
                'content': '''# Формы в Django

Django предоставляет мощные инструменты для работы с формами.

## Создание формы

```python
from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)
```

## Форма на основе модели

```python
from django.forms import ModelForm
from .models import Post

class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'category']
```

## Обработка формы во view

```python
def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Обработка данных
            name = form.cleaned_data['name']
            # Сохранение в базу или отправка email
            return redirect('success')
    else:
        form = ContactForm()
    
    return render(request, 'contact.html', {'form': form})
```

## Шаблон формы

```html
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Отправить</button>
</form>
```''',
                'lesson_type': 'lecture',
                'order': 9
            },
            {
                'title': 'Практика: Создание формы',
                'content': '''# Практическое задание: Создание формы

Создайте форму для добавления постов в блог:

1. Создайте ModelForm для модели Post
2. Создайте view для отображения и обработки формы
3. Создайте шаблон с формой
4. Добавьте валидацию полей

**Требования:**
- Форма должна включать поля: title, content, category
- Добавьте валидацию: title должен быть не менее 5 символов
- После успешного сохранения перенаправляйте на страницу поста
- Используйте `{{ form.as_p }}` для отображения формы''',
                'lesson_type': 'practice',
                'order': 10,
                'practice_code_template': '# forms.py\nfrom django import forms\nfrom .models import Post\n\nclass PostForm(forms.ModelForm):\n    class Meta:\n        model = Post\n        fields = [\'title\', \'content\', \'category\']\n    \n    # Добавьте валидацию\n\n# views.py\ndef create_post(request):\n    # Обработка формы\n    pass'
            },
            {
                'title': 'Аутентификация пользователей',
                'content': '''# Аутентификация пользователей в Django

Django предоставляет встроенную систему аутентификации пользователей.

## Настройка

В `settings.py` убедитесь, что есть:
```python
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    # ...
]

MIDDLEWARE = [
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # ...
]
```

## Регистрация пользователей

```python
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})
```

## Вход и выход

```python
from django.contrib.auth import authenticate, login, logout

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
    return render(request, 'registration/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')
```

## Защита views

```python
from django.contrib.auth.decorators import login_required

@login_required
def create_post(request):
    # Только для авторизованных пользователей
    pass
```''',
                'lesson_type': 'lecture',
                'order': 11
            },
            {
                'title': 'Практика: Аутентификация',
                'content': '''# Практическое задание: Аутентификация

Добавьте систему аутентификации в блог:

1. Создайте views для регистрации, входа и выхода
2. Создайте шаблоны для форм регистрации и входа
3. Защитите view создания постов декоратором @login_required
4. Добавьте отображение имени текущего пользователя в навигации

**Требования:**
- Используйте встроенные формы Django для регистрации
- После регистрации автоматически выполняйте вход
- После выхода перенаправляйте на главную страницу
- В навигации показывайте "Привет, username!" для авторизованных пользователей''',
                'lesson_type': 'practice',
                'order': 12,
                'practice_code_template': '# views.py\nfrom django.contrib.auth.forms import UserCreationForm\nfrom django.contrib.auth import login, authenticate, logout\nfrom django.contrib.auth.decorators import login_required\n\n# Создайте views для регистрации, входа, выхода\n# Защитите создание постов декоратором @login_required\n\ndef register(request):\n    pass\n\ndef login_view(request):\n    pass\n\ndef logout_view(request):\n    pass\n\n@login_required\ndef create_post(request):\n    pass'
            },
            {
                'title': 'Работа с медиафайлами',
                'content': '''# Работа с медиафайлами в Django

Django позволяет легко работать с загружаемыми файлами.

## Настройка

В `settings.py`:
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

В `urls.py`:
```python
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

## Модель с файлами

```python
class Post(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='posts/', blank=True)
    document = models.FileField(upload_to='documents/', blank=True)
```

## Форма с файлами

```python
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'image', 'document']
        widgets = {
            'image': forms.FileInput(attrs={'accept': 'image/*'}),
        }
```

## Обработка во view

```python
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('post_list')
    else:
        form = PostForm()
    return render(request, 'create_post.html', {'form': form})
```

## Отображение в шаблоне

```html
{% if post.image %}
    <img src="{{ post.image.url }}" alt="{{ post.title }}">
{% endif %}

{% if post.document %}
    <a href="{{ post.document.url }}">Скачать документ</a>
{% endif %}
```''',
                'lesson_type': 'lecture',
                'order': 13
            },
            {
                'title': 'Практика: Загрузка изображений',
                'content': '''# Практическое задание: Загрузка изображений

Добавьте возможность загрузки изображений к постам:

1. Добавьте поле image в модель Post
2. Обновите форму PostForm для работы с файлами
3. Измените view create_post для обработки файлов
4. Отобразите изображения в шаблонах

**Требования:**
- Изображения должны сохраняться в папку media/posts/
- Добавьте валидацию типов файлов (только изображения)
- Отображайте изображения в списке постов и на странице деталей
- Добавьте размер изображения в шаблоне (например, width="300")''',
                'lesson_type': 'practice',
                'order': 14,
                'practice_code_template': '# models.py\nclass Post(models.Model):\n    # Добавьте поле image\n    # image = models.ImageField(...)\n    pass\n\n# forms.py\nclass PostForm(forms.ModelForm):\n    class Meta:\n        model = Post\n        fields = [\'title\', \'content\', \'category\', \'image\']\n        # Добавьте widgets для валидации\n\n# views.py\ndef create_post(request):\n    # Обработайте request.FILES\n    pass'
            },
            {
                'title': 'Пагинация',
                'content': '''# Пагинация в Django

Пагинация позволяет разбивать большие списки данных на страницы.

## Использование в views

```python
from django.core.paginator import Paginator

def post_list(request):
    posts = Post.objects.all()
    paginator = Paginator(posts, 5)  # 5 постов на страницу
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'post_list.html', {'page_obj': page_obj})
```

## В шаблоне

```html
<!-- Список постов -->
{% for post in page_obj %}
    <div class="post">
        <h3>{{ post.title }}</h3>
        <p>{{ post.content|truncatewords:30 }}</p>
    </div>
{% endfor %}

<!-- Навигация по страницам -->
<div class="pagination">
    {% if page_obj.has_previous %}
        <a href="?page=1">&laquo; Первая</a>
        <a href="?page={{ page_obj.previous_page_number }}">Предыдущая</a>
    {% endif %}
    
    <span>Страница {{ page_obj.number }} из {{ page_obj.paginator.num_pages }}</span>
    
    {% if page_obj.has_next %}
        <a href="?page={{ page_obj.next_page_number }}">Следующая</a>
        <a href="?page={{ page_obj.paginator.num_pages }}">Последняя &raquo;</a>
    {% endif %}
</div>
```

## Стилизация

```css
.pagination {
    display: flex;
    justify-content: center;
    margin: 20px 0;
}

.pagination a, .pagination span {
    padding: 8px 12px;
    margin: 0 4px;
    text-decoration: none;
    border: 1px solid #ddd;
}

.pagination a:hover {
    background-color: #f5f5f5;
}
```''',
                'lesson_type': 'lecture',
                'order': 15
            },
            {
                'title': 'Практика: Пагинация',
                'content': '''# Практическое задание: Пагинация

Добавьте пагинацию к списку постов:

1. Измените view post_list для использования Paginator
2. Настройте отображение 3 постов на страницу
3. Добавьте навигацию по страницам в шаблоне
4. Стилизуйте пагинацию

**Требования:**
- Показывайте по 3 поста на странице
- Добавьте ссылки "Предыдущая" и "Следующая"
- Покажите номер текущей страницы и общее количество страниц
- Стилизуйте пагинацию с помощью CSS''',
                'lesson_type': 'practice',
                'order': 16,
                'practice_code_template': '# views.py\nfrom django.core.paginator import Paginator\n\ndef post_list(request):\n    # Используйте Paginator\n    # posts = Post.objects.all()\n    # paginator = Paginator(posts, 3)\n    pass\n\n<!-- post_list.html -->\n<!-- Добавьте пагинацию -->\n<!-- {% for post in page_obj %} -->\n<!-- {% if page_obj.has_previous %} -->'
            },
            {
                'title': 'Поиск и фильтрация',
                'content': '''# Поиск и фильтрация в Django

Django предоставляет мощные инструменты для поиска и фильтрации данных.

## Базовая фильтрация

```python
# Поиск по точному совпадению
posts = Post.objects.filter(title='Заголовок')

# Поиск по части строки
posts = Post.objects.filter(title__contains='Python')

# Поиск с игнорированием регистра
posts = Post.objects.filter(title__icontains='python')

# Поиск по дате
recent_posts = Post.objects.filter(created_date__gte=timezone.now() - timedelta(days=7))

# Поиск по внешнему ключу
category_posts = Post.objects.filter(category__name='Технологии')
```

## Сложные запросы

```python
from django.db.models import Q

# ИЛИ условие
posts = Post.objects.filter(
    Q(title__icontains='Python') | Q(content__icontains='Python')
)

# И условие
posts = Post.objects.filter(
    Q(title__icontains='Python') & Q(is_published=True)
)

# Исключение
posts = Post.objects.exclude(category__name='Черновики')
```

## Поиск во view

```python
def search(request):
    query = request.GET.get('q')
    posts = Post.objects.all()
    
    if query:
        posts = posts.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )
    
    return render(request, 'search_results.html', {'posts': posts, 'query': query})
```

## Шаблон поиска

```html
<form method="get" action="{% url 'search' %}">
    <input type="text" name="q" value="{{ query }}" placeholder="Поиск...">
    <button type="submit">Найти</button>
</form>
```''',
                'lesson_type': 'lecture',
                'order': 17
            },
            {
                'title': 'Практика: Поиск по блогу',
                'content': '''# Практическое задание: Поиск по блогу

Добавьте функцию поиска по блогу:

1. Создайте view для поиска постов
2. Добавьте форму поиска в навигацию
3. Реализуйте поиск по заголовку и содержанию постов
4. Отобразите результаты поиска

**Требования:**
- Поиск должен работать по заголовку и содержанию постов
- Игнорировать регистр при поиске
- Показывать количество найденных результатов
- Если поисковый запрос пустой, показывать все посты''',
                'lesson_type': 'practice',
                'order': 18,
                'practice_code_template': '# views.py\ndef search(request):\n    # Получите поисковый запрос из GET параметров\n    # Выполните поиск по заголовку и содержанию\n    # Верните результаты\n    pass\n\n<!-- base.html -->\n<!-- Добавьте форму поиска в навигацию -->\n<!-- <form method="get" action="{% url \'search\' %}"> -->'
            },
            {
                'title': 'Комментарии',
                'content': '''# Комментарии в Django

Добавим систему комментариев к постам блога.

## Модель комментариев

```python
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.CharField(max_length=100)
    email = models.EmailField()
    content = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_date']
    
    def __str__(self):
        return f'Комментарий от {self.author} к {self.post.title}'
```

## Форма комментариев

```python
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['author', 'email', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
        }
```

## View для комментариев

```python
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.save()
            return redirect('post_detail', post_id=post.id)
    else:
        form = CommentForm()
    
    return render(request, 'post_detail.html', {
        'post': post,
        'form': form,
        'comments': post.comments.filter(is_approved=True)
    })
```

## Шаблон комментариев

```html
<!-- Отображение комментариев -->
<div class="comments">
    <h3>Комментарии ({{ comments.count }})</h3>
    {% for comment in comments %}
        <div class="comment">
            <p><strong>{{ comment.author }}</strong> ({{ comment.created_date }})</p>
            <p>{{ comment.content }}</p>
        </div>
    {% endfor %}
</div>

<!-- Форма добавления комментария -->
<div class="add-comment">
    <h4>Добавить комментарий</h4>
    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit">Отправить</button>
    </form>
</div>
```''',
                'lesson_type': 'lecture',
                'order': 19
            },
            {
                'title': 'Практика: Система комментариев',
                'content': '''# Практическое задание: Система комментариев

Добавьте систему комментариев к блогу:

1. Создайте модель Comment
2. Создайте форму CommentForm
3. Обновите view post_detail для обработки комментариев
4. Добавьте отображение комментариев в шаблон

**Требования:**
- Комментарии должны быть привязаны к постам
- Все комментарии по умолчанию не одобрены
- Показывайте только одобренные комментарии
- Добавьте форму для новых комментариев на странице поста''',
                'lesson_type': 'practice',
                'order': 20,
                'practice_code_template': '# models.py\nclass Comment(models.Model):\n    # Создайте модель комментариев\n    # post = ForeignKey(Post, ...)\n    # author = CharField(...)\n    # content = TextField(...)\n    pass\n\n# forms.py\nclass CommentForm(forms.ModelForm):\n    class Meta:\n        model = Comment\n        fields = [\'author\', \'email\', \'content\']\n\n# views.py\ndef post_detail(request, post_id):\n    # Добавьте обработку комментариев\n    pass'
            },
            {
                'title': 'API с Django REST Framework',
                'content': '''# API с Django REST Framework

Django REST Framework (DRF) позволяет создавать мощные веб-API.

## Установка

```bash
pip install djangorestframework
```

В `settings.py`:
```python
INSTALLED_APPS = [
    'rest_framework',
    # ...
]
```

## Сериализаторы

```python
from rest_framework import serializers
from .models import Post

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'created_date', 'is_published']
```

## ViewSets

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
```

## URLs API

```python
from rest_framework.routers import DefaultRouter
from .views import PostViewSet

router = DefaultRouter()
router.register(r'posts', PostViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
```

## Аутентификация API

В `settings.py`:
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

## Использование API

Получение списка постов:
```bash
curl -H "Authorization: Token your_token" http://127.0.0.1:8000/api/posts/
```

Создание нового поста:
```bash
curl -X POST -H "Authorization: Token your_token" -H "Content-Type: application/json" -d '{"title":"Новый пост","content":"Содержание поста"}' http://127.0.0.1:8000/api/posts/
```''',
                'lesson_type': 'lecture',
                'order': 21
            },
            {
                'title': 'Практика: Создание API',
                'content': '''# Практическое задание: Создание API

Создайте REST API для блога:

1. Установите Django REST Framework
2. Создайте сериализаторы для Post и Category
3. Создайте ViewSets для Post и Category
4. Настройте URLs для API
5. Добавьте аутентификацию по токенам

**Требования:**
- API должно включать endpoints для posts и categories
- Добавьте фильтрацию по опубликованным постам
- Реализуйте CRUD операции
- Защитите API аутентификацией по токенам''',
                'lesson_type': 'practice',
                'order': 22,
                'practice_code_template': '# serializers.py\nfrom rest_framework import serializers\nfrom .models import Post, Category\n\nclass PostSerializer(serializers.ModelSerializer):\n    class Meta:\n        model = Post\n        fields = \'__all__\'\n\n# views.py\nfrom rest_framework import viewsets\n\nclass PostViewSet(viewsets.ModelViewSet):\n    queryset = Post.objects.all()\n    serializer_class = PostSerializer\n\n# urls.py\nfrom rest_framework.routers import DefaultRouter\n# Настройте роутинг для API'
            },
            {
                'title': 'Тестирование Django приложений',
                'content': '''# Тестирование Django приложений

Тестирование — важная часть разработки, которая помогает убедиться в корректности работы приложения.

## Базовая структура тестов

В файле `tests.py`:
```python
from django.test import TestCase
from django.urls import reverse
from .models import Post, Category

class PostModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Тестовая категория',
            description='Описание категории'
        )
        self.post = Post.objects.create(
            title='Тестовый пост',
            content='Содержание тестового поста',
            category=self.category
        )
    
    def test_post_creation(self):
        self.assertEqual(self.post.title, 'Тестовый пост')
        self.assertTrue(self.post.created_date)
    
    def test_string_representation(self):
        self.assertEqual(str(self.post), 'Тестовый пост')
```

## Тестирование Views

```python
class PostViewTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Категория')
        self.post = Post.objects.create(
            title='Пост',
            content='Содержание',
            category=self.category
        )
    
    def test_post_list_view(self):
        response = self.client.get(reverse('post_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Пост')
    
    def test_post_detail_view(self):
        response = self.client.get(
            reverse('post_detail', args=(self.post.id,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Пост')
```

## Тестирование Forms

```python
class PostFormTest(TestCase):
    def test_valid_form(self):
        category = Category.objects.create(name='Категория')
        data = {
            'title': 'Новый пост',
            'content': 'Содержание поста',
            'category': category.id
        }
        form = PostForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_form(self):
        form = PostForm(data={})
        self.assertFalse(form.is_valid())
```

## Запуск тестов

```bash
python manage.py test
python manage.py test blog.tests.PostModelTest
python manage.py test blog.tests.PostModelTest.test_post_creation
```''',
                'lesson_type': 'lecture',
                'order': 23
            },
            {
                'title': 'Практика: Написание тестов',
                'content': '''# Практическое задание: Написание тестов

Напишите тесты для блога:

1. Создайте тесты для моделей Post и Category
2. Напишите тесты для views post_list и post_detail
3. Создайте тесты для формы PostForm
4. Добавьте тесты для поиска

**Требования:**
- Проверьте создание моделей
- Проверьте отображение страниц
- Проверьте валидацию форм
- Проверьте работу поиска с разными запросами
- Убедитесь, что тесты проходят успешно''',
                'lesson_type': 'practice',
                'order': 24,
                'practice_code_template': '# tests.py\nfrom django.test import TestCase\nfrom django.urls import reverse\nfrom .models import Post, Category\nfrom .forms import PostForm\n\nclass PostModelTest(TestCase):\n    def setUp(self):\n        # Создайте тестовые данные\n        pass\n    \n    def test_post_creation(self):\n        # Проверьте создание поста\n        pass\n    \n    def test_string_representation(self):\n        # Проверьте строковое представление\n        pass\n\nclass PostViewTest(TestCase):\n    def test_post_list_view(self):\n        # Проверьте отображение списка постов\n        pass\n\nclass PostFormTest(TestCase):\n    def test_valid_form(self):\n        # Проверьте валидную форму\n        pass'
            },
            {
                'title': 'Развертывание Django приложений',
                'content': '''# Развертывание Django приложений

Развертывание — процесс подготовки приложения для работы на production сервере.

## Подготовка к развертыванию

1. Установите DEBUG=False в settings.py
2. Настройте ALLOWED_HOSTS
3. Используйте environment variables для секретных данных
4. Соберите статические файлы

```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Использование environment variables
import os
SECRET_KEY = os.environ.get('SECRET_KEY')
DATABASE_URL = os.environ.get('DATABASE_URL')
```

## Статические файлы

```python
# settings.py
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

Сбор статических файлов:
```bash
python manage.py collectstatic
```

## WSGI сервер

Установка Gunicorn:
```bash
pip install gunicorn
```

Запуск:
```bash
gunicorn myproject.wsgi:application
```

## Nginx конфигурация

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /static/ {
        alias /path/to/your/project/staticfiles/;
    }

    location /media/ {
        alias /path/to/your/project/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Docker

Dockerfile:
```dockerfile
FROM python:3.9

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8000"]
```''',
                'lesson_type': 'lecture',
                'order': 25
            },
            {
                'title': 'Практика: Подготовка к развертыванию',
                'content': '''# Практическое задание: Подготовка к развертыванию

Подготовьте блог к развертыванию:

1. Создайте production settings
2. Настройте environment variables
3. Подготовьте сбор статических файлов
4. Создайте Dockerfile

**Требования:**
- Создайте отдельный settings файл для production
- Используйте environment variables для SECRET_KEY и DEBUG
- Настройте STATIC_ROOT и MEDIA_ROOT
- Создайте Dockerfile для контейнеризации приложения
- Добавьте requirements.txt с зависимостями''',
                'lesson_type': 'practice',
                'order': 26,
                'practice_code_template': '# settings/production.py\nimport os\nfrom .base import *\n\nDEBUG = False\nALLOWED_HOSTS = [\'*\']  # Для тестирования\n\nSECRET_KEY = os.environ.get(\'SECRET_KEY\')\n\nSTATIC_ROOT = os.path.join(BASE_DIR, \'staticfiles\')\nMEDIA_ROOT = os.path.join(BASE_DIR, \'media\')\n\n# Dockerfile\n# FROM python:3.9\n# WORKDIR /app\n# COPY requirements.txt .\n# RUN pip install -r requirements.txt\n# COPY . .'
            }
        ]
        
        # Создать уроки
        for lesson_data in lessons_data:
            # Поддержка нового формата test_cases и старого формата test_input/test_output
            test_cases = lesson_data.get('test_cases', [])
            if not test_cases and lesson_data.get('test_input') and lesson_data.get('test_output'):
                # Конвертируем старый формат в новый
                test_cases = [{
                    'input': lesson_data.get('test_input', ''),
                    'output': lesson_data.get('test_output', '')
                }]
            
            lesson, created = Lesson.objects.get_or_create(
                course=course,
                title=lesson_data['title'],
                defaults={
                    'content': lesson_data['content'],
                    'lesson_type': lesson_data['lesson_type'],
                    'order': lesson_data['order'],
                    'practice_code_template': lesson_data.get('practice_code_template', ''),
                    'test_cases': test_cases,
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Создан урок: {lesson.title}'))
            else:
                self.stdout.write(self.style.WARNING(f'  Урок уже существует: {lesson.title}'))
        
        self.stdout.write(self.style.SUCCESS(f'\nКурс "{course.title}" успешно создан с {len(lessons_data)} уроками!'))