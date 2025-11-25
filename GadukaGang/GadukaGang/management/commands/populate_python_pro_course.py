from django.core.management.base import BaseCommand
from GadukaGang.models import Course, Lesson

class Command(BaseCommand):
    help = 'Создает курс Python для профессионалов с заданиями на проверку вывода'

    def handle(self, *args, **options):
        # Создать или получить курс Python для профессионалов
        course, created = Course.objects.get_or_create(
            title='Python для профессионалов',
            defaults={
                'description': 'Профессиональный курс по Python. Сложные алгоритмы, оптимизация, работа с большими данными.',
                'order': 3,
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
                'title': 'Алгоритмы сортировки',
                'content': '''# Алгоритмы сортировки

## Быстрая сортировка (Quick Sort)

Быстрая сортировка использует стратегию "разделяй и властвуй".

```python
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
```

## Сортировка слиянием (Merge Sort)

```python
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
```''',
                'lesson_type': 'lecture',
                'order': 1
            },
            {
                'title': 'Практика: Реализация быстрой сортировки',
                'content': '''# Практическое задание: Реализация быстрой сортировки

Реализуйте алгоритм быстрой сортировки для сортировки списка чисел по возрастанию.

Программа должна:
1. Принимать список чисел через input (числа разделены пробелами)
2. Сортировать числа по возрастанию используя быструю сортировку
3. Выводить отсортированный список, числа разделены пробелами

**Пример входных данных:**
```
64 34 25 12 22 11 90
```

**Ожидаемый вывод:**
```
11 12 22 25 34 64 90
```''',
                'lesson_type': 'practice',
                'order': 2,
                'practice_code_template': '# Введите код здесь\n# Реализуйте функцию быстрой сортировки\n',
                'test_cases': [
                    {'input': '64 34 25 12 22 11 90', 'output': '11 12 22 25 34 64 90'},
                    {'input': '5 4 3 2 1', 'output': '1 2 3 4 5'},
                    {'input': '1', 'output': '1'},
                    {'input': '10 20 30', 'output': '10 20 30'},
                    {'input': '50 30 40 20 10', 'output': '10 20 30 40 50'},
                    {'input': '100 50 75 25', 'output': '25 50 75 100'},
                    {'input': '3 1 4 1 5 9 2 6', 'output': '1 1 2 3 4 5 6 9'},
                    {'input': '99 88 77 66', 'output': '66 77 88 99'},
                    {'input': '42', 'output': '42'},
                    {'input': '15 7 23 9 31 5', 'output': '5 7 9 15 23 31'}
                ]
            },
            {
                'title': 'Поиск в графах',
                'content': '''# Поиск в графах

## Поиск в глубину (DFS)

```python
def dfs(graph, start, visited=None):
    if visited is None:
        visited = set()
    visited.add(start)
    print(start)
    for neighbor in graph[start]:
        if neighbor not in visited:
            dfs(graph, neighbor, visited)
```

## Поиск в ширину (BFS)

```python
from collections import deque

def bfs(graph, start):
    visited = set()
    queue = deque([start])
    visited.add(start)
    while queue:
        node = queue.popleft()
        print(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
```''',
                'lesson_type': 'lecture',
                'order': 3
            },
            {
                'title': 'Практика: Поиск кратчайшего пути',
                'content': '''# Практическое задание: Поиск кратчайшего пути

Напишите программу, которая находит кратчайший путь между двумя узлами в графе.

Входные данные:
- Первая строка: количество узлов n
- Следующие n строк: для каждого узла список соседей (индексы разделены пробелами, индексация с 0)
- Последняя строка: начальный и конечный узел (разделены пробелом)

Выведите последовательность узлов кратчайшего пути, разделенных пробелами.

**Пример входных данных:**
```
5
1 2
0 2 3
0 1 4
1 4
2 3
0 4
```

**Ожидаемый вывод:**
```
0 1 3 4
```''',
                'lesson_type': 'practice',
                'order': 4,
                'practice_code_template': '# Введите код здесь\n# Реализуйте BFS для поиска кратчайшего пути\n',
                'test_cases': [
                    {'input': '5\n1 2\n0 2 3\n0 1 4\n1 4\n2 3\n0 4', 'output': '0 1 3 4'},
                    {'input': '3\n1 2\n0 2\n0 1\n0 2', 'output': '0 2'},
                    {'input': '4\n1\n0 2\n1 3\n2\n0 3', 'output': '0 1 2 3'},
                    {'input': '2\n1\n0\n0 1', 'output': '0 1'},
                    {'input': '6\n1 2\n0 3\n0 4\n1 5\n2 5\n3 4\n0 5', 'output': '0 1 3 5'},
                    {'input': '3\n1\n0 2\n1\n0 2', 'output': '0 1 2'},
                    {'input': '4\n1 2 3\n0\n0\n0\n0 3', 'output': '0 3'},
                    {'input': '5\n1\n0 2\n1 3\n2 4\n3\n0 4', 'output': '0 1 2 3 4'},
                    {'input': '2\n1\n0\n0 1', 'output': '0 1'},
                    {'input': '4\n1 2\n0 3\n0 3\n1 2\n0 3', 'output': '0 1 3'}
                ]
            },
            {
                'title': 'Динамическое программирование',
                'content': '''# Динамическое программирование

Динамическое программирование - это техника решения задач путем разбиения их на подзадачи.

## Задача о рюкзаке

```python
def knapsack(weights, values, capacity):
    n = len(weights)
    dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for w in range(1, capacity + 1):
            if weights[i-1] <= w:
                dp[i][w] = max(
                    dp[i-1][w],
                    dp[i-1][w-weights[i-1]] + values[i-1]
                )
            else:
                dp[i][w] = dp[i-1][w]
    
    return dp[n][capacity]
```

## Числа Фибоначчи с мемоизацией

```python
def fibonacci_memo(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fibonacci_memo(n-1, memo) + fibonacci_memo(n-2, memo)
    return memo[n]
```''',
                'lesson_type': 'lecture',
                'order': 5
            },
            {
                'title': 'Практика: Задача о рюкзаке',
                'content': '''# Практическое задание: Задача о рюкзаке

Реализуйте решение задачи о рюкзаке (0/1).

Входные данные:
- Первая строка: количество предметов n и вместимость рюкзака W (разделены пробелом)
- Следующие n строк: вес и стоимость предмета (разделены пробелом)

Выведите максимальную стоимость, которую можно унести в рюкзаке.

**Пример входных данных:**
```
3 50
10 60
20 100
30 120
```

**Ожидаемый вывод:**
```
220
```''',
                'lesson_type': 'practice',
                'order': 6,
                'practice_code_template': '# Введите код здесь\n# Реализуйте решение задачи о рюкзаке\n',
                'test_cases': [
                    {'input': '3 50\n10 60\n20 100\n30 120', 'output': '220'},
                    {'input': '2 10\n5 10\n5 10', 'output': '10'},
                    {'input': '1 5\n3 7', 'output': '7'},
                    {'input': '4 10\n2 3\n3 4\n4 5\n5 6', 'output': '10'},
                    {'input': '3 15\n5 10\n10 20\n15 30', 'output': '30'},
                    {'input': '2 20\n10 15\n15 25', 'output': '25'},
                    {'input': '5 100\n20 30\n30 40\n40 50\n50 60\n60 70', 'output': '100'},
                    {'input': '1 10\n10 20', 'output': '20'},
                    {'input': '3 30\n10 20\n15 25\n20 30', 'output': '50'},
                    {'input': '4 25\n5 10\n10 15\n15 20\n20 25', 'output': '35'}
                ]
            },
            {
                'title': 'Обработка больших данных',
                'content': '''# Обработка больших данных

## Генераторы

Генераторы позволяют создавать последовательности без хранения всех элементов в памяти.

```python
def fibonacci_generator():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# Использование
fib = fibonacci_generator()
for i in range(10):
    print(next(fib))
```

## Генераторные выражения

```python
squares = (x**2 for x in range(10))
sum_squares = sum(squares)
```

## Обработка потоков данных

```python
def process_stream(stream):
    for chunk in stream:
        yield process_chunk(chunk)
```''',
                'lesson_type': 'lecture',
                'order': 7
            },
            {
                'title': 'Практика: Генератор простых чисел',
                'content': '''# Практическое задание: Генератор простых чисел

Создайте генератор, который генерирует простые числа.

Программа должна:
1. Принимать число n через input
2. Генерировать первые n простых чисел
3. Выводить их, разделенные пробелами

**Пример входных данных:**
```
10
```

**Ожидаемый вывод:**
```
2 3 5 7 11 13 17 19 23 29
```''',
                'lesson_type': 'practice',
                'order': 8,
                'practice_code_template': '# Введите код здесь\n# Создайте генератор простых чисел\n',
                'test_cases': [
                    {'input': '10', 'output': '2 3 5 7 11 13 17 19 23 29'},
                    {'input': '1', 'output': '2'},
                    {'input': '5', 'output': '2 3 5 7 11'},
                    {'input': '3', 'output': '2 3 5'},
                    {'input': '15', 'output': '2 3 5 7 11 13 17 19 23 29 31 37 41 43 47'},
                    {'input': '7', 'output': '2 3 5 7 11 13 17'},
                    {'input': '20', 'output': '2 3 5 7 11 13 17 19 23 29 31 37 41 43 47 53 59 61 67 71'},
                    {'input': '2', 'output': '2 3'},
                    {'input': '12', 'output': '2 3 5 7 11 13 17 19 23 29 31 37'},
                    {'input': '8', 'output': '2 3 5 7 11 13 17 19'}
                ]
            },
            {
                'title': 'Оптимизация производительности',
                'content': '''# Оптимизация производительности

## Профилирование кода

```python
import cProfile
import pstats

def my_function():
    # ваш код
    pass

cProfile.run('my_function()')
```

## Кэширование

```python
from functools import lru_cache

@lru_cache(maxsize=None)
def expensive_function(n):
    # сложные вычисления
    return result
```

## Использование встроенных функций

Встроенные функции Python часто быстрее, чем циклы:

```python
# Медленно
result = []
for x in range(1000):
    result.append(x * 2)

# Быстро
result = [x * 2 for x in range(1000)]
```''',
                'lesson_type': 'lecture',
                'order': 9
            },
            {
                'title': 'Практика: Оптимизированная обработка',
                'content': '''# Практическое задание: Оптимизированная обработка

Напишите программу, которая:
1. Принимает список чисел через input (числа разделены пробелами)
2. Находит все числа, которые являются квадратами других чисел в списке
3. Выводит найденные числа, отсортированные по возрастанию, разделенные пробелами
4. Если таких чисел нет, выведите "Нет"

**Пример входных данных:**
```
1 2 3 4 5 9 16 25
```

**Ожидаемый вывод:**
```
4 9 16 25
```

(4=2², 9=3², 16=4², 25=5²)''',
                'lesson_type': 'practice',
                'order': 10,
                'practice_code_template': '# Введите код здесь\n# Оптимизируйте решение\n',
                'test_cases': [
                    {'input': '1 2 3 4 5 9 16 25', 'output': '4 9 16 25'},
                    {'input': '1 4 9', 'output': '4 9'},
                    {'input': '1 2 3', 'output': 'Нет'},
                    {'input': '1 4 9 16 25 36', 'output': '4 9 16 25 36'},
                    {'input': '1', 'output': 'Нет'},
                    {'input': '4 9 16', 'output': '4 9 16'},
                    {'input': '1 2 4 8 16', 'output': '4 16'},
                    {'input': '9 25 49', 'output': '9 25 49'},
                    {'input': '1 2 3 4 5 6 7 8 9', 'output': '4 9'},
                    {'input': '16 25 36 49 64', 'output': '16 25 36 49 64'}
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

