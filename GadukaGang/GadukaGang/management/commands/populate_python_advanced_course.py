from django.core.management.base import BaseCommand
from GadukaGang.models import Course, Lesson

class Command(BaseCommand):
    help = 'Создает курс Python для продвинутых с заданиями на проверку вывода'

    def handle(self, *args, **options):
        # Создать или получить курс Python для продвинутых
        course, created = Course.objects.get_or_create(
            title='Python для продвинутых',
            defaults={
                'description': 'Продвинутый курс по Python. Работа с алгоритмами, структурами данных и сложными задачами.',
                'order': 2,
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
                    {'input': '1 2 3', 'output': '3\n2\n1'},
                    {'input': '10 5 20 15', 'output': '20\n15\n10\n5'},
                    {'input': '100', 'output': '100'},
                    {'input': '7 3 9 1 5', 'output': '9\n7\n5\n3\n1'},
                    {'input': '0 0 0', 'output': '0\n0\n0'},
                    {'input': '-5 -2 -8 -1', 'output': '-1\n-2\n-5\n-8'},
                    {'input': '42 17 99 33 66', 'output': '99\n66\n42\n33\n17'},
                    {'input': '1', 'output': '1'},
                    {'input': '50 25 75 10 90 5', 'output': '90\n75\n50\n25\n10\n5'}
                ]
            },
            {
                'title': 'Словари и множества',
                'content': '''# Словари и множества

## Словари (Dictionaries)

Словари - это структуры данных типа ключ-значение.

```python
person = {
    "name": "Иван",
    "age": 25,
    "city": "Москва"
}

# Доступ к значениям
print(person["name"])  # Иван
print(person.get("age", 0))  # 25, или 0 если ключа нет

# Итерация
for key, value in person.items():
    print(f"{key}: {value}")
```

## Множества (Sets)

Множества хранят уникальные элементы.

```python
numbers = {1, 2, 3, 4, 5}
numbers.add(6)  # Добавить элемент
numbers.remove(3)  # Удалить элемент

# Операции с множествами
set1 = {1, 2, 3}
set2 = {3, 4, 5}
union = set1 | set2  # Объединение
intersection = set1 & set2  # Пересечение
```''',
                'lesson_type': 'lecture',
                'order': 3
            },
            {
                'title': 'Практика: Подсчет частоты элементов',
                'content': '''# Практическое задание: Подсчет частоты элементов

Напишите программу, которая:
1. Принимает строку слов через input (слова разделены пробелами)
2. Подсчитывает частоту каждого слова
3. Выводит каждое слово и его частоту в формате: "слово: количество" (каждая пара на новой строке)
4. Слова должны быть отсортированы по алфавиту

**Пример входных данных:**
```
яблоко банан яблоко апельсин банан яблоко
```

**Ожидаемый вывод:**
```
апельсин: 1
банан: 2
яблоко: 3
```''',
                'lesson_type': 'practice',
                'order': 4,
                'practice_code_template': '# Введите код здесь\n# Используйте словарь для подсчета частоты\n',
                'test_cases': [
                    {'input': 'яблоко банан яблоко апельсин банан яблоко', 'output': 'апельсин: 1\nбанан: 2\nяблоко: 3'},
                    {'input': 'кот собака кот', 'output': 'кот: 2\nсобака: 1'},
                    {'input': 'один два три', 'output': 'два: 1\nодин: 1\nтри: 1'},
                    {'input': 'а а а а', 'output': 'а: 4'},
                    {'input': 'hello world hello', 'output': 'hello: 2\nworld: 1'},
                    {'input': 'python java python cpp java python', 'output': 'cpp: 1\njava: 2\npython: 3'},
                    {'input': 'x y z x y x', 'output': 'x: 3\ny: 2\nz: 1'},
                    {'input': 'test', 'output': 'test: 1'},
                    {'input': 'a b c a b a', 'output': 'a: 3\nb: 2\nc: 1'},
                    {'input': 'один один два два три', 'output': 'два: 2\nодин: 2\nтри: 1'}
                ]
            },
            {
                'title': 'Обработка строк',
                'content': '''# Обработка строк

## Методы строк

```python
text = "  Hello, World!  "
text.strip()  # Убрать пробелы с краев
text.upper()  # Верхний регистр
text.lower()  # Нижний регистр
text.replace("Hello", "Hi")  # Замена
text.split(",")  # Разделить по разделителю
```

## Форматирование

```python
name = "Иван"
age = 25
message = f"Меня зовут {name}, мне {age} лет"
```

## Работа с символами

```python
text = "Python"
for char in text:
    print(char)

# Проверка
text.isalpha()  # Только буквы
text.isdigit()  # Только цифры
text.isalnum()  # Буквы и цифры
```''',
                'lesson_type': 'lecture',
                'order': 5
            },
            {
                'title': 'Практика: Обработка текста',
                'content': '''# Практическое задание: Обработка текста

Напишите программу, которая:
1. Принимает строку через input
2. Удаляет все пробелы из строки
3. Преобразует все буквы в верхний регистр
4. Выводит результат

**Пример входных данных:**
```
Hello World Python
```

**Ожидаемый вывод:**
```
HELLOWORLDPYTHON
```''',
                'lesson_type': 'practice',
                'order': 6,
                'practice_code_template': '# Введите код здесь\n',
                'test_cases': [
                    {'input': 'Hello World Python', 'output': 'HELLOWORLDPYTHON'},
                    {'input': 'test string', 'output': 'TESTSTRING'},
                    {'input': 'a b c', 'output': 'ABC'},
                    {'input': 'Python Programming', 'output': 'PYTHONPROGRAMMING'},
                    {'input': 'hello', 'output': 'HELLO'},
                    {'input': '  spaces  ', 'output': 'SPACES'},
                    {'input': 'MiXeD CaSe', 'output': 'MIXEDCASE'},
                    {'input': '123 abc 456', 'output': '123ABC456'},
                    {'input': 'one two three', 'output': 'ONETWOTHREE'},
                    {'input': 'A', 'output': 'A'}
                ]
            },
            {
                'title': 'Рекурсия',
                'content': '''# Рекурсия

Рекурсия - это техника, когда функция вызывает сама себя.

## Пример: Факториал

```python
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
```

## Пример: Числа Фибоначчи

```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
```

## Важно

- Всегда должно быть базовое условие (когда рекурсия останавливается)
- Рекурсия может быть неэффективной для больших значений
- Используйте мемоизацию для оптимизации''',
                'lesson_type': 'lecture',
                'order': 7
            },
            {
                'title': 'Практика: Рекурсивная сумма',
                'content': '''# Практическое задание: Рекурсивная сумма

Напишите рекурсивную функцию `sum_digits(n)`, которая:
1. Принимает целое число n
2. Возвращает сумму всех цифр числа
3. Если число отрицательное, работайте с его абсолютным значением

Затем в основной программе:
- Примите число через input
- Вызовите функцию sum_digits
- Выведите результат

**Пример входных данных:**
```
12345
```

**Ожидаемый вывод:**
```
15
```

(1+2+3+4+5 = 15)''',
                'lesson_type': 'practice',
                'order': 8,
                'practice_code_template': '# Введите код здесь\n# Создайте рекурсивную функцию sum_digits\n',
                'test_cases': [
                    {'input': '12345', 'output': '15'},
                    {'input': '0', 'output': '0'},
                    {'input': '999', 'output': '27'},
                    {'input': '10', 'output': '1'},
                    {'input': '111', 'output': '3'},
                    {'input': '987654321', 'output': '45'},
                    {'input': '100', 'output': '1'},
                    {'input': '42', 'output': '6'},
                    {'input': '7', 'output': '7'},
                    {'input': '123456789', 'output': '45'}
                ]
            },
            {
                'title': 'Работа с файлами',
                'content': '''# Работа с файлами

## Чтение файлов

```python
# Чтение всего файла
with open('file.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Чтение построчно
with open('file.txt', 'r', encoding='utf-8') as f:
    for line in f:
        print(line.strip())
```

## Запись в файлы

```python
with open('output.txt', 'w', encoding='utf-8') as f:
    f.write("Hello, World!")
```

## Режимы открытия

- `'r'` - чтение
- `'w'` - запись (перезапись)
- `'a'` - добавление
- `'r+'` - чтение и запись''',
                'lesson_type': 'lecture',
                'order': 9
            },
            {
                'title': 'Практика: Обработка данных',
                'content': '''# Практическое задание: Обработка данных

Напишите программу, которая:
1. Принимает через input список чисел, разделенных пробелами
2. Находит максимальное и минимальное значение
3. Вычисляет среднее арифметическое (округлить до 2 знаков после запятой)
4. Выводит результат в формате:
   ```
   Максимум: <макс>
   Минимум: <мин>
   Среднее: <среднее>
   ```

**Пример входных данных:**
```
10 20 30 40 50
```

**Ожидаемый вывод:**
```
Максимум: 50
Минимум: 10
Среднее: 30.0
```''',
                'lesson_type': 'practice',
                'order': 10,
                'practice_code_template': '# Введите код здесь\n',
                'test_cases': [
                    {'input': '10 20 30 40 50', 'output': 'Максимум: 50\nМинимум: 10\nСреднее: 30.0'},
                    {'input': '5', 'output': 'Максимум: 5\nМинимум: 5\nСреднее: 5.0'},
                    {'input': '1 2 3', 'output': 'Максимум: 3\nМинимум: 1\nСреднее: 2.0'},
                    {'input': '100 200 300', 'output': 'Максимум: 300\nМинимум: 100\nСреднее: 200.0'},
                    {'input': '0 0 0 0', 'output': 'Максимум: 0\nМинимум: 0\nСреднее: 0.0'},
                    {'input': '15 25 35', 'output': 'Максимум: 35\nМинимум: 15\nСреднее: 25.0'},
                    {'input': '1 10 100', 'output': 'Максимум: 100\nМинимум: 1\nСреднее: 37.0'},
                    {'input': '50 50 50', 'output': 'Максимум: 50\nМинимум: 50\nСреднее: 50.0'},
                    {'input': '2 4 6 8 10', 'output': 'Максимум: 10\nМинимум: 2\nСреднее: 6.0'},
                    {'input': '99 1', 'output': 'Максимум: 99\nМинимум: 1\nСреднее: 50.0'}
                ]
            },
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

