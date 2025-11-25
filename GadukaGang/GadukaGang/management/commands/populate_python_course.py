from django.core.management.base import BaseCommand
from GadukaGang.models import Course, Lesson

class Command(BaseCommand):
    help = 'Создает курс Python с лекциями и практическими заданиями'

    def handle(self, *args, **options):
        # Создать или получить курс Python
        course, created = Course.objects.get_or_create(
            title='Python для начинающих',
            defaults={
                'description': 'Подробный курс по основам Python. Изучите переменные, типы данных, циклы и многое другое.',
                'order': 1,
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
                'practice_code_template': '# Создайте переменные здесь\nname = ""\nage = 0\nfavorite_language = ""\n\n# Выведите информацию\nprint("Имя:", name)\nprint("Возраст:", age)\nprint("Любимый язык:", favorite_language)'
            },
            {
                'title': 'Типы данных',
                'content': '''# Типы данных в Python

Python имеет несколько встроенных типов данных:

## Основные типы:

### 1. Числа (Numbers)
- **int** — целые числа: `42`, `-10`, `0`
- **float** — дробные числа: `3.14`, `-0.5`, `2.0`

### 2. Строки (Strings)
Строки — это последовательности символов:
```python
text = "Привет, мир!"
message = 'Это тоже строка'
```

### 3. Булевы значения (Boolean)
```python
is_true = True
is_false = False
```

### 4. Списки (Lists)
Списки — это упорядоченные коллекции элементов:
```python
numbers = [1, 2, 3, 4, 5]
fruits = ["яблоко", "банан", "апельсин"]
```

### 5. Словари (Dictionaries)
Словари хранят пары ключ-значение:
```python
person = {
    "name": "Иван",
    "age": 25,
    "city": "Москва"
}
```

## Проверка типа данных

Используйте функцию `type()` для проверки типа:
```python
x = 42
print(type(x))  # <class 'int'>
```''',
                'lesson_type': 'lecture',
                'order': 4
            },
            {
                'title': 'Вывод данных',
                'content': '''# Вывод данных в Python

Функция `print()` используется для вывода данных на экран.

## Базовое использование

```python
print("Hello, World!")
print(42)
print(3.14)
```

## Вывод нескольких значений

```python
name = "Иван"
age = 25
print("Имя:", name, "Возраст:", age)
```

## Форматирование строк

### 1. f-строки (рекомендуется)
```python
name = "Иван"
age = 25
print(f"Меня зовут {name}, мне {age} лет")
```

### 2. Метод format()
```python
print("Меня зовут {}, мне {} лет".format(name, age))
```

### 3. % форматирование
```python
print("Меня зовут %s, мне %d лет" % (name, age))
```

## Специальные символы

```python
print("Первая строка\\nВторая строка")  # Перевод строки
print("Табуляция\\tтекст")  # Табуляция
```''',
                'lesson_type': 'lecture',
                'order': 5
            },
            {
                'title': 'Практика: Вывод данных',
                'content': '''# Практическое задание: Вывод данных

Создайте программу, которая выводит информацию о книге:
- Название книги
- Автор
- Год издания
- Количество страниц

Используйте f-строки для форматирования вывода.''',
                'lesson_type': 'practice',
                'order': 6,
                'practice_code_template': '# Создайте переменные для книги\nbook_title = ""\nauthor = ""\nyear = 0\npages = 0\n\n# Выведите информацию используя f-строки\nprint(f"Название: {book_title}")\nprint(f"Автор: {author}")\nprint(f"Год: {year}")\nprint(f"Страниц: {pages}")'
            },
            {
                'title': 'Условные операторы',
                'content': '''# Условные операторы

Условные операторы позволяют выполнять код в зависимости от условий.

## Оператор if

```python
age = 18
if age >= 18:
    print("Вы совершеннолетний")
```

## if-else

```python
age = 15
if age >= 18:
    print("Вы совершеннолетний")
else:
    print("Вы несовершеннолетний")
```

## if-elif-else

```python
score = 85
if score >= 90:
    print("Отлично!")
elif score >= 70:
    print("Хорошо!")
elif score >= 50:
    print("Удовлетворительно")
else:
    print("Нужно подтянуть")
```

## Логические операторы

- `and` — и
- `or` — или
- `not` — не

```python
age = 25
has_license = True

if age >= 18 and has_license:
    print("Можно водить машину")
```''',
                'lesson_type': 'lecture',
                'order': 7
            },
            {
                'title': 'Циклы',
                'content': '''# Циклы в Python

Циклы позволяют выполнять код несколько раз.

## Цикл for

Цикл `for` используется для перебора элементов:

```python
# Перебор списка
fruits = ["яблоко", "банан", "апельсин"]
for fruit in fruits:
    print(fruit)
```

### Функция range()

```python
# Перебор чисел от 0 до 4
for i in range(5):
    print(i)

# От 1 до 10
for i in range(1, 11):
    print(i)

# С шагом 2
for i in range(0, 10, 2):
    print(i)
```

## Цикл while

Цикл `while` выполняется, пока условие истинно:

```python
count = 0
while count < 5:
    print(count)
    count += 1
```

## Управление циклами

- `break` — прервать цикл
- `continue` — перейти к следующей итерации

```python
for i in range(10):
    if i == 5:
        break  # Прервать цикл
    print(i)
```''',
                'lesson_type': 'lecture',
                'order': 8
            },
            {
                'title': 'Практика: Циклы',
                'content': '''# Практическое задание: Циклы

Напишите программу, которая:
1. Выводит все четные числа от 0 до 20
2. Вычисляет сумму чисел от 1 до 100
3. Выводит таблицу умножения на 5 (от 1 до 10)''',
                'lesson_type': 'practice',
                'order': 9,
                'practice_code_template': '# 1. Четные числа от 0 до 20\nprint("Четные числа:")\nfor i in range(0, 21, 2):\n    print(i)\n\n# 2. Сумма чисел от 1 до 100\nsum = 0\nfor i in range(1, 101):\n    sum += i\nprint(f"Сумма: {sum}")\n\n# 3. Таблица умножения на 5\nprint("Таблица умножения на 5:")\nfor i in range(1, 11):\n    print(f"5 x {i} = {5 * i}")'
            },
            {
                'title': 'Функции',
                'content': '''# Функции в Python

Функции позволяют группировать код для повторного использования.

## Определение функции

```python
def greet():
    print("Привет, мир!")

greet()  # Вызов функции
```

## Функции с параметрами

```python
def greet(name):
    print(f"Привет, {name}!")

greet("Иван")
```

## Функции с возвращаемым значением

```python
def add(a, b):
    return a + b

result = add(5, 3)
print(result)  # 8
```

## Параметры по умолчанию

```python
def greet(name, greeting="Привет"):
    print(f"{greeting}, {name}!")

greet("Иван")  # Привет, Иван!
greet("Иван", "Здравствуй")  # Здравствуй, Иван!
```

## Локальные и глобальные переменные

```python
x = 10  # Глобальная переменная

def my_function():
    y = 5  # Локальная переменная
    print(x)  # Можно использовать глобальную
    print(y)

my_function()
```''',
                'lesson_type': 'lecture',
                'order': 10
            },
            {
                'title': 'Практика: Функции',
                'content': '''# Практическое задание: Функции

Создайте функции:
1. `calculate_area(length, width)` — вычисляет площадь прямоугольника
2. `is_even(number)` — проверяет, является ли число четным
3. `factorial(n)` — вычисляет факториал числа n''',
                'lesson_type': 'practice',
                'order': 11,
                'practice_code_template': '# 1. Функция для вычисления площади\n\ndef calculate_area(length, width):\n    # Ваш код здесь\n    pass\n\n# 2. Функция для проверки четности\n\ndef is_even(number):\n    # Ваш код здесь\n    pass\n\n# 3. Функция для вычисления факториала\n\ndef factorial(n):\n    # Ваш код здесь\n    pass\n\n# Тестирование\nprint(calculate_area(5, 3))  # Должно быть 15\nprint(is_even(4))  # Должно быть True\nprint(factorial(5))  # Должно быть 120'
            },
        ]
        
        # Создать уроки
        for lesson_data in lessons_data:
            lesson, created = Lesson.objects.get_or_create(
                course=course,
                title=lesson_data['title'],
                defaults={
                    'content': lesson_data['content'],
                    'lesson_type': lesson_data['lesson_type'],
                    'order': lesson_data['order'],
                    'practice_code_template': lesson_data.get('practice_code_template', ''),
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Создан урок: {lesson.title}'))
            else:
                self.stdout.write(self.style.WARNING(f'  Урок уже существует: {lesson.title}'))
        
        self.stdout.write(self.style.SUCCESS(f'\\nКурс "{course.title}" успешно создан с {len(lessons_data)} уроками!'))

