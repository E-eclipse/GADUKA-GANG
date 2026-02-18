from django.core.management.base import BaseCommand
from GadukaGang.models import Course, Lesson

class Command(BaseCommand):
    help = 'Создает курс Data Science с Python с лекциями и практическими заданиями'

    def handle(self, *args, **options):
        # Создать или получить курс Data Science
        course, created = Course.objects.get_or_create(
            title='Data Science с Python',
            defaults={
                'description': 'Полный курс по анализу данных с использованием Python. Изучите pandas, numpy, matplotlib, seaborn и другие библиотеки для работы с данными.',
                'order': 5,
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
                'title': 'Введение в Data Science',
                'content': '''# Введение в Data Science

Data Science — это междисциплинарная область, которая использует научные методы, процессы, алгоритмы и системы для извлечения знаний из структурированных и неструктурированных данных.

## Что такое Data Science?

Data Science сочетает в себе:
- Статистику и математику
- Программирование
- Экспертные знания в предметной области
- Визуализацию данных

## Процесс Data Science

1. **Постановка вопроса** - определение проблемы
2. **Сбор данных** - получение необходимых данных
3. **Очистка данных** - подготовка данных к анализу
4. **Анализ данных** - исследование и моделирование
5. **Интерпретация результатов** - выводы и рекомендации

## Основные библиотеки Python

- **NumPy** - работа с многомерными массивами
- **Pandas** - анализ и манипуляция данными
- **Matplotlib** - визуализация данных
- **Seaborn** - статистическая визуализация
- **Scikit-learn** - машинное обучение

## Ваше первое исследование

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Создание простого датасета
data = {
    'month': ['Янв', 'Фев', 'Мар', 'Апр', 'Май'],
    'sales': [100, 150, 120, 200, 180]
}
df = pd.DataFrame(data)

# Простая визуализация
plt.plot(df['month'], df['sales'])
plt.title('Продажи по месяцам')
plt.xlabel('Месяц')
plt.ylabel('Продажи')
plt.show()
```''',
                'lesson_type': 'lecture',
                'order': 1
            },
            {
                'title': 'Практика: Установка библиотек',
                'content': '''# Практическое задание: Установка библиотек

Установите необходимые библиотеки для Data Science:

1. Установите Anaconda или отдельные библиотеки:
   - NumPy
   - Pandas
   - Matplotlib
   - Seaborn
   - Jupyter Notebook

2. Создайте Jupyter Notebook
3. Импортируйте все библиотеки
4. Проверьте версии установленных библиотек

**Подсказки:**
- Используйте команду `pip install` или `conda install`
- Для проверки версий используйте `pd.__version__`, `np.__version__` и т.д.
- Jupyter Notebook запускается командой `jupyter notebook`''',
                'lesson_type': 'practice',
                'order': 2,
                'practice_code_template': '# Установите библиотеки и проверьте их версии\nimport numpy as np\nimport pandas as pd\nimport matplotlib.pyplot as plt\nimport seaborn as sns\n\n# Выведите версии библиотек\nprint("NumPy version:", np.__version__)\nprint("Pandas version:", pd.__version__)'
            },
            {
                'title': 'NumPy: Основы',
                'content': '''# NumPy: Основы

NumPy (Numerical Python) — это фундаментальный пакет для научных вычислений в Python.

## Создание массивов

```python
import numpy as np

# Создание массива из списка
arr = np.array([1, 2, 3, 4, 5])

# Создание массива с нулями
zeros = np.zeros(5)

# Создание массива с единицами
ones = np.ones((3, 3))

# Создание массива с равномерно распределенными значениями
range_arr = np.arange(0, 10, 2)  # [0, 2, 4, 6, 8]

# Создание массива с линейно распределенными значениями
linear = np.linspace(0, 1, 5)  # [0.0, 0.25, 0.5, 0.75, 1.0]
```

## Атрибуты массивов

```python
arr = np.array([[1, 2, 3], [4, 5, 6]])

print(arr.shape)    # (2, 3) - форма массива
print(arr.size)     # 6 - общее количество элементов
print(arr.ndim)     # 2 - количество измерений
print(arr.dtype)    # int64 - тип данных
```

## Индексация и срезы

```python
arr = np.array([10, 20, 30, 40, 50])

# Индексация
print(arr[0])       # 10
print(arr[-1])      # 50

# Срезы
print(arr[1:4])     # [20, 30, 40]
print(arr[:3])      # [10, 20, 30]
print(arr[::2])     # [10, 30, 50] - каждый второй элемент

# Для многомерных массивов
matrix = np.array([[1, 2, 3], [4, 5, 6]])
print(matrix[0, 1])     # 2
print(matrix[:, 1])     # [2, 5] - второй столбец
```

## Основные операции

```python
arr1 = np.array([1, 2, 3])
arr2 = np.array([4, 5, 6])

# Поэлементные операции
print(arr1 + arr2)      # [5, 7, 9]
print(arr1 * arr2)      # [4, 10, 18]
print(arr1 ** 2)        # [1, 4, 9]

# Математические функции
print(np.sqrt(arr1))    # [1.0, 1.414, 1.732]
print(np.sum(arr1))     # 6
print(np.mean(arr1))    # 2.0
```''',
                'lesson_type': 'lecture',
                'order': 3
            },
            {
                'title': 'Практика: Работа с массивами NumPy',
                'content': '''# Практическое задание: Работа с массивами NumPy

Создайте и манипулируйте массивами NumPy:

1. Создайте одномерный массив с числами от 1 до 20
2. Создайте двумерный массив 4x5 с числами от 1 до 20
3. Найдите сумму, среднее, минимум и максимум для обоих массивов
4. Выберите каждый третий элемент из первого массива
5. Выберите вторую строку и третий столбец из второго массива

**Подсказки:**
- Используйте `np.arange()` для создания массивов
- Используйте `reshape()` для изменения формы массива
- Для нахождения статистик используйте `np.sum()`, `np.mean()`, `np.min()`, `np.max()`''',
                'lesson_type': 'practice',
                'order': 4,
                'practice_code_template': '# Создайте массивы и выполните операции\nimport numpy as np\n\n# 1. Одномерный массив от 1 до 20\narr1d = np.arange(1, 21)\nprint("1D array:", arr1d)\n\n# 2. Двумерный массив 4x5\narr2d = np.arange(1, 21).reshape(4, 5)\nprint("2D array:\\n", arr2d)\n\n# 3. Статистики\nprint("Sum 1D:", np.sum(arr1d))\nprint("Mean 1D:", np.mean(arr1d))\n# Добавьте остальные статистики\n\n# 4. Каждый третий элемент\n# print("Every third element:", arr1d[::3])\n\n# 5. Вторая строка и третий столбец\n# print("Second row:", arr2d[1, :])\n# print("Third column:", arr2d[:, 2])'
            },
            {
                'title': 'Pandas: Основы',
                'content': '''# Pandas: Основы

Pandas — это библиотека для анализа данных, предоставляющая удобные структуры данных и функции для работы с данными.

## Структуры данных

### Series

Series — одномерный массив с метками (индексами).

```python
import pandas as pd

# Создание Series из списка
s = pd.Series([1, 3, 5, 7, 9])
print(s)

# Создание Series с пользовательскими индексами
s = pd.Series([1, 3, 5, 7, 9], index=['a', 'b', 'c', 'd', 'e'])
print(s['c'])  # 5

# Создание Series из словаря
s = pd.Series({'apple': 5, 'banana': 3, 'orange': 8})
print(s['apple'])  # 5
```

### DataFrame

DataFrame — двумерная таблица с метками для строк и столбцов.

```python
# Создание DataFrame из словаря
data = {
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'city': ['New York', 'London', 'Tokyo']
}
df = pd.DataFrame(data)
print(df)

# Создание DataFrame из списка списков
data = [['Alice', 25], ['Bob', 30], ['Charlie', 35]]
df = pd.DataFrame(data, columns=['name', 'age'])
print(df)
```

## Базовые операции

```python
# Просмотр данных
print(df.head())        # Первые 5 строк
print(df.tail(3))       # Последние 3 строки
print(df.info())        # Информация о DataFrame
print(df.describe())    # Статистическое описание

# Выбор столбцов
print(df['name'])       # Выбор одного столбца
print(df[['name', 'age']])  # Выбор нескольких столбцов

# Выбор строк
print(df.iloc[0])       # По позиции
print(df.loc[0])        # По индексу

# Фильтрация
filtered = df[df['age'] > 25]
print(filtered)
```''',
                'lesson_type': 'lecture',
                'order': 5
            },
            {
                'title': 'Практика: Работа с DataFrame',
                'content': '''# Практическое задание: Работа с DataFrame

Создайте DataFrame и выполните базовые операции:

1. Создайте DataFrame с данными о студентах:
   - Имя (name)
   - Возраст (age)
   - Оценка (grade)
   - Город (city)

2. Добавьте еще 5 студентов в DataFrame
3. Выведите первые 3 строки и последние 2 строки
4. Покажите статистическое описание числовых данных
5. Отфильтруйте студентов с оценкой выше 80
6. Отсортируйте по возрасту по убыванию

**Подсказки:**
- Используйте `pd.DataFrame()` для создания DataFrame
- Для добавления строк используйте `pd.concat()` или `append()`
- Для фильтрации используйте булевы маски
- Для сортировки используйте `sort_values()`''',
                'lesson_type': 'practice',
                'order': 6,
                'practice_code_template': '# Создайте DataFrame и выполните операции\nimport pandas as pd\n\n# 1. Создайте DataFrame со студентами\ndata = {\n    \'name\': [\'Alice\', \'Bob\', \'Charlie\'],\n    \'age\': [20, 22, 21],\n    \'grade\': [85, 92, 78],\n    \'city\': [\'New York\', \'London\', \'Tokyo\']\n}\ndf = pd.DataFrame(data)\nprint("Original DataFrame:\\n", df)\n\n# 2. Добавьте еще 5 студентов\n# new_students = pd.DataFrame({...})\n# df = pd.concat([df, new_students], ignore_index=True)\n\n# 3. Выведите первые 3 и последние 2 строки\n# print("First 3 rows:\\n", df.head(3))\n\n# 4. Статистическое описание\n# print("Statistics:\\n", df.describe())\n\n# 5. Фильтрация студентов с оценкой > 80\n# high_grade_students = df[df[\'grade\'] > 80]\n\n# 6. Сортировка по возрасту по убыванию\n# sorted_df = df.sort_values(\'age\', ascending=False)'
            },
            {
                'title': 'Загрузка и очистка данных',
                'content': '''# Загрузка и очистка данных

Работа с реальными данными часто требует их загрузки и очистки.

## Загрузка данных

```python
# Из CSV файла
df = pd.read_csv('data.csv')

# Из Excel файла
df = pd.read_excel('data.xlsx')

# Из JSON
df = pd.read_json('data.json')

# Из базы данных
import sqlite3
conn = sqlite3.connect('database.db')
df = pd.read_sql_query("SELECT * FROM table_name", conn)
```

## Осмотр данных

```python
# Базовая информация
print(df.info())        # Типы данных, пропущенные значения
print(df.shape)         # Размерность
print(df.columns)       # Названия столбцов
print(df.dtypes)        # Типы данных столбцов

# Проверка пропущенных значений
print(df.isnull().sum())  # Количество пропущенных значений по столбцам
print(df.isna().any())    # Есть ли пропущенные значения в каждом столбце
```

## Обработка пропущенных значений

```python
# Удаление строк с пропущенными значениями
df_clean = df.dropna()

# Удаление столбцов с пропущенными значениями
df_clean = df.dropna(axis=1)

# Заполнение пропущенных значений
df['column'].fillna(0, inplace=True)              # Нулями
df['column'].fillna(df['column'].mean(), inplace=True)  # Средним значением
df['column'].fillna(method='ffill', inplace=True) # Предыдущим значением

# Интерполяция
df['column'].interpolate(inplace=True)
```

## Удаление дубликатов

```python
# Проверка наличия дубликатов
print(df.duplicated().sum())

# Удаление дубликатов
df_clean = df.drop_duplicates()

# Удаление дубликатов по определенным столбцам
df_clean = df.drop_duplicates(subset=['name', 'email'])
```

## Преобразование данных

```python
# Преобразование типов данных
df['age'] = df['age'].astype(int)
df['price'] = pd.to_numeric(df['price'], errors='coerce')

# Создание новых столбцов
df['full_name'] = df['first_name'] + ' ' + df['last_name']
df['age_group'] = pd.cut(df['age'], bins=[0, 18, 35, 60, 100], labels=['Child', 'Young', 'Adult', 'Senior'])

# Замена значений
df['gender'] = df['gender'].replace({'M': 'Male', 'F': 'Female'})
```''',
                'lesson_type': 'lecture',
                'order': 7
            },
            {
                'title': 'Практика: Очистка данных',
                'content': '''# Практическое задание: Очистка данных

Очистите набор данных о продажах:

1. Загрузите данные из CSV файла (предоставляется)
2. Проверьте наличие пропущенных значений
3. Заполните пропущенные значения в числовых столбцах средним значением
4. Удалите строки с пропущенными значениями в текстовых столбцах
5. Удалите дубликаты
6. Преобразуйте столбец даты в правильный формат
7. Создайте новый столбец с категорией цены (низкая, средняя, высокая)

**Подсказки:**
- Используйте `pd.read_csv()` для загрузки данных
- Для заполнения используйте `fillna()` с `mean()`
- Для удаления дубликатов используйте `drop_duplicates()`
- Для преобразования дат используйте `pd.to_datetime()`
- Для категоризации используйте `pd.cut()` или условия''',
                'lesson_type': 'practice',
                'order': 8,
                'practice_code_template': '# Очистите данные о продажах\nimport pandas as pd\nimport numpy as np\n\n# Создайте пример данных для практики\ndata = {\n    \'product\': [\'A\', \'B\', \'C\', \'A\', \'B\', None, \'C\'],\n    \'price\': [100, 250, np.nan, 120, 300, 180, 200],\n    \'quantity\': [10, 5, 8, 12, np.nan, 15, 7],\n    \'date\': [\'2023-01-15\', \'2023-01-16\', \'2023-01-17\', \'2023-01-15\', \'2023-01-18\', \'2023-01-19\', \'2023-01-20\'],\n    \'customer\': [\'John\', \'Alice\', \'Bob\', \'John\', \'Charlie\', \'David\', \'Bob\']\n}\ndf = pd.DataFrame(data)\nprint("Original data:\\n", df)\n\n# 1. Проверьте пропущенные значения\n# print("Missing values:\\n", df.isnull().sum())\n\n# 2. Заполните пропущенные значения в числовых столбцах\n# numeric_columns = df.select_dtypes(include=[np.number]).columns\n# for col in numeric_columns:\n#     df[col].fillna(df[col].mean(), inplace=True)\n\n# 3. Удалите строки с пропущенными значениями в текстовых столбцах\n# df.dropna(subset=[\'product\'], inplace=True)\n\n# 4. Удалите дубликаты\n# df.drop_duplicates(inplace=True)\n\n# 5. Преобразуйте дату\n# df[\'date\'] = pd.to_datetime(df[\'date\'])\n\n# 6. Создайте категорию цены\n# price_bins = [0, 150, 250, 1000]\n# price_labels = [\'Low\', \'Medium\', \'High\']\n# df[\'price_category\'] = pd.cut(df[\'price\'], bins=price_bins, labels=price_labels)'
            },
            {
                'title': 'Агрегация и группировка данных',
                'content': '''# Агрегация и группировка данных

Агрегация и группировка позволяют извлекать сводную информацию из данных.

## Агрегатные функции

```python
# Базовые агрегатные функции
print(df['price'].sum())        # Сумма
print(df['price'].mean())       # Среднее
print(df['price'].median())     # Медиана
print(df['price'].std())        # Стандартное отклонение
print(df['price'].min())        # Минимум
print(df['price'].max())        # Максимум

# Несколько агрегатов сразу
print(df.agg({
    'price': ['sum', 'mean', 'std'],
    'quantity': ['sum', 'count']
}))
```

## Группировка данных

```python
# Группировка по одному столбцу
grouped = df.groupby('category')
print(grouped['price'].mean())

# Группировка по нескольким столбцам
grouped = df.groupby(['category', 'region'])
print(grouped['price'].sum())

# Агрегатные функции после группировки
result = df.groupby('category').agg({
    'price': ['mean', 'sum'],
    'quantity': 'sum',
    'product': 'count'
})

# Переименование столбцов
result.columns = ['avg_price', 'total_price', 'total_quantity', 'product_count']
```

## Сводные таблицы

```python
# Создание сводной таблицы
pivot = df.pivot_table(
    values='price',           # Значения для агрегации
    index='category',         # Строки
    columns='region',         # Столбцы
    aggfunc='mean',           # Функция агрегации
    fill_value=0             # Значение для пропущенных данных
)

# Сводная таблица с несколькими значениями
pivot = df.pivot_table(
    values=['price', 'quantity'],
    index='category',
    columns='region',
    aggfunc={'price': 'mean', 'quantity': 'sum'}
)
```

## Объединение данных

```python
# Конкатенация (вертикальное объединение)
df_combined = pd.concat([df1, df2], ignore_index=True)

# Объединение по ключу (JOIN)
df_merged = pd.merge(df1, df2, on='key_column', how='inner')

# Объединение по индексу
df_merged = df1.join(df2, how='left')
```

## Преобразование данных

```python
# Преобразование "широкий" -> "длинный" формат
df_long = df.melt(
    id_vars=['product'],           # Столбцы, которые остаются
    value_vars=['jan', 'feb', 'mar'],  # Столбцы для преобразования
    var_name='month',              # Имя нового столбца для имен переменных
    value_name='sales'             # Имя нового столбца для значений
)

# Преобразование "длинный" -> "широкий" формат
df_wide = df_long.pivot(
    index='product',
    columns='month',
    values='sales'
)
```''',
                'lesson_type': 'lecture',
                'order': 9
            },
            {
                'title': 'Практика: Агрегация и группировка',
                'content': '''# Практическое задание: Агрегация и группировка

Проанализируйте данные о продажах:

1. Создайте DataFrame с данными о продажах:
   - Продукт (product)
   - Категория (category)
   - Регион (region)
   - Цена (price)
   - Количество (quantity)
   - Дата (date)

2. Рассчитайте общую выручку по каждой категории
3. Найдите среднюю цену по регионам
4. Определите самый продаваемый продукт по количеству
5. Создайте сводную таблицу с выручкой по категориям и регионам
6. Преобразуйте данные из широкого в длинный формат

**Подсказки:**
- Выручка = цена * количество
- Используйте `groupby()` для группировки
- Для сводных таблиц используйте `pivot_table()`
- Для преобразования форматов используйте `melt()` и `pivot()`''',
                'lesson_type': 'practice',
                'order': 10,
                'practice_code_template': '# Анализ данных о продажах\nimport pandas as pd\nimport numpy as np\n\n# 1. Создайте данные о продажах\ndata = {\n    \'product\': [\'A\', \'B\', \'C\', \'A\', \'B\', \'C\', \'A\', \'B\'],\n    \'category\': [\'Electronics\', \'Clothing\', \'Electronics\', \'Electronics\', \'Clothing\', \'Electronics\', \'Clothing\', \'Electronics\'],\n    \'region\': [\'North\', \'South\', \'North\', \'South\', \'North\', \'South\', \'North\', \'South\'],\n    \'price\': [100, 50, 120, 110, 55, 125, 60, 115],\n    \'quantity\': [10, 20, 15, 8, 25, 12, 18, 9]\n}\ndf = pd.DataFrame(data)\nprint("Sales data:\\n", df)\n\n# 2. Выручка по категориям\n# df[\'revenue\'] = df[\'price\'] * df[\'quantity\']\n# revenue_by_category = df.groupby(\'category\')[\'revenue\'].sum()\n\n# 3. Средняя цена по регионам\n# avg_price_by_region = df.groupby(\'region\')[\'price\'].mean()\n\n# 4. Самый продаваемый продукт\n# top_product = df.groupby(\'product\')[\'quantity\'].sum().idxmax()\n\n# 5. Сводная таблица\n# pivot_table = df.pivot_table(values=\'revenue\', index=\'category\', columns=\'region\', aggfunc=\'sum\', fill_value=0)\n\n# 6. Преобразование формата\n# Добавьте столбцы для месяцев и преобразуйте с помощью melt()'
            },
            {
                'title': 'Визуализация данных с Matplotlib',
                'content': '''# Визуализация данных с Matplotlib

Matplotlib — это библиотека для создания статических, анимированных и интерактивных визуализаций в Python.

## Основы Matplotlib

```python
import matplotlib.pyplot as plt
import numpy as np

# Простой график
x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(10, 6))
plt.plot(x, y)
plt.title('График синуса')
plt.xlabel('X')
plt.ylabel('Y')
plt.grid(True)
plt.show()
```

## Типы графиков

### Линейные графики

```python
# Несколько линий
x = np.linspace(0, 10, 100)
y1 = np.sin(x)
y2 = np.cos(x)

plt.figure(figsize=(10, 6))
plt.plot(x, y1, label='sin(x)', linewidth=2)
plt.plot(x, y2, label='cos(x)', linestyle='--', linewidth=2)
plt.legend()
plt.title('Тригонометрические функции')
plt.xlabel('X')
plt.ylabel('Y')
plt.grid(True)
plt.show()
```

### Гистограммы

```python
# Простая гистограмма
data = np.random.normal(100, 15, 1000)

plt.figure(figsize=(10, 6))
plt.hist(data, bins=30, alpha=0.7, color='blue', edgecolor='black')
plt.title('Распределение данных')
plt.xlabel('Значения')
plt.ylabel('Частота')
plt.grid(True, alpha=0.3)
plt.show()
```

### Диаграммы рассеяния

```python
# Диаграмма рассеяния
x = np.random.randn(100)
y = np.random.randn(100)

plt.figure(figsize=(8, 6))
plt.scatter(x, y, alpha=0.6, c='red')
plt.title('Диаграмма рассеяния')
plt.xlabel('X')
plt.ylabel('Y')
plt.grid(True, alpha=0.3)
plt.show()
```

### Столбчатые диаграммы

```python
# Вертикальные столбцы
categories = ['A', 'B', 'C', 'D']
values = [23, 45, 56, 78]

plt.figure(figsize=(8, 6))
plt.bar(categories, values, color=['red', 'green', 'blue', 'orange'])
plt.title('Столбчатая диаграмма')
plt.xlabel('Категории')
plt.ylabel('Значения')
plt.show()
```

## Настройка графиков

```python
# Цвета и стили
plt.figure(figsize=(12, 8))

# Подграфики
plt.subplot(2, 2, 1)
plt.plot(x, y1, 'r-', linewidth=2)
plt.title('График 1')

plt.subplot(2, 2, 2)
plt.hist(data, bins=20, color='green', alpha=0.7)
plt.title('Гистограмма')

plt.subplot(2, 2, 3)
plt.scatter(x, y, c='purple', alpha=0.6)
plt.title('Диаграмма рассеяния')

plt.subplot(2, 2, 4)
plt.bar(categories, values, color='orange')
plt.title('Столбчатая диаграмма')

plt.tight_layout()  # Автоматическая настройка расположения
plt.show()
```

## Сохранение графиков

```python
plt.figure(figsize=(10, 6))
plt.plot(x, y)
plt.title('Мой график')
plt.savefig('my_plot.png', dpi=300, bbox_inches='tight')
plt.show()
```''',
                'lesson_type': 'lecture',
                'order': 11
            },
            {
                'title': 'Практика: Создание визуализаций',
                'content': '''# Практическое задание: Создание визуализаций

Создайте различные типы графиков для анализа данных:

1. Создайте набор данных о продажах за год (месяцы и значения продаж)
2. Постройте линейный график продаж по месяцам
3. Создайте гистограмму распределения продаж
4. Постройте столбчатую диаграмму продаж по кварталам
5. Создайте диаграмму рассеяния для анализа зависимости цены и количества
6. Объедините несколько графиков в одной фигуре

**Подсказки:**
- Используйте `np.linspace()` и `np.random` для создания данных
- Для столбчатых диаграмм используйте `plt.bar()`
- Для гистограмм используйте `plt.hist()`
- Для диаграмм рассеяния используйте `plt.scatter()`
- Используйте `plt.subplot()` для создания подграфиков''',
                'lesson_type': 'practice',
                'order': 12,
                'practice_code_template': '# Создайте визуализации\nimport matplotlib.pyplot as plt\nimport numpy as np\n\n# 1. Данные о продажах\nmonths = [\'Янв\', \'Фев\', \'Мар\', \'Апр\', \'Май\', \'Июн\', \n          \'Июл\', \'Авг\', \'Сен\', \'Окт\', \'Ноя\', \'Дек\']\nsales = np.random.randint(80, 200, 12)\n\n# 2. Линейный график\nplt.figure(figsize=(12, 8))\nplt.subplot(2, 2, 1)\n# plt.plot(months, sales, marker=\'o\')\n# plt.title(\'Продажи по месяцам\')\n\n# 3. Гистограмма\nplt.subplot(2, 2, 2)\n# plt.hist(sales, bins=5, alpha=0.7, color=\'blue\')\n# plt.title(\'Распределение продаж\')\n\n# 4. Столбчатая диаграмма по кварталам\nplt.subplot(2, 2, 3)\n# quarters = [\'Q1\', \'Q2\', \'Q3\', \'Q4\']\n# quarterly_sales = [sum(sales[:3]), sum(sales[3:6]), sum(sales[6:9]), sum(sales[9:])]\n# plt.bar(quarters, quarterly_sales, color=[\'red\', \'green\', \'blue\', \'orange\'])\n# plt.title(\'Продажи по кварталам\')\n\n# 5. Диаграмма рассеяния\nplt.subplot(2, 2, 4)\n# prices = np.random.randint(50, 150, 50)\n# quantities = np.random.randint(1, 100, 50)\n# plt.scatter(prices, quantities, alpha=0.6)\n# plt.title(\'Зависимость цены и количества\')\n# plt.xlabel(\'Цена\')\n# plt.ylabel(\'Количество\')\n\nplt.tight_layout()\nplt.show()'
            },
            {
                'title': 'Визуализация данных с Seaborn',
                'content': '''# Визуализация данных с Seaborn

Seaborn — это библиотека для создания статистических графиков на основе Matplotlib с более привлекательным оформлением.

## Основы Seaborn

```python
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Установка стиля
sns.set_style("whitegrid")
plt.figure(figsize=(10, 6))

# Загрузка встроенных данных
tips = sns.load_dataset("tips")
print(tips.head())
```

## Статистические графики

### Распределения

```python
# Гистограмма с плотностью распределения
plt.figure(figsize=(12, 4))

plt.subplot(1, 2, 1)
sns.histplot(tips['total_bill'], kde=True)
plt.title('Распределение общего счета')

plt.subplot(1, 2, 2)
sns.boxplot(y=tips['total_bill'])
plt.title('Ящик с усами')

plt.tight_layout()
plt.show()
```

### Корреляции

```python
# Тепловая карта корреляций
plt.figure(figsize=(10, 8))
correlation_matrix = tips.select_dtypes(include=[np.number]).corr()
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0)
plt.title('Матрица корреляций')
plt.show()
```

### Сравнения

```python
# Столбчатая диаграмма со средними значениями
plt.figure(figsize=(10, 6))
sns.barplot(data=tips, x='day', y='total_bill', ci=95)
plt.title('Средний счет по дням недели')
plt.show()

# Ящик с усами по категориям
plt.figure(figsize=(10, 6))
sns.boxplot(data=tips, x='day', y='total_bill')
plt.title('Распределение счетов по дням недели')
plt.xticks(rotation=45)
plt.show()
```

## Многомерные графики

### Диаграммы рассеяния

```python
# Диаграмма рассеяния с цветовой кодировкой
plt.figure(figsize=(10, 6))
sns.scatterplot(data=tips, x='total_bill', y='tip', hue='time', style='sex')
plt.title('Чаевые vs Общий счет')
plt.show()

# Пара графиков (pairplot)
sns.pairplot(tips[['total_bill', 'tip', 'size']], diag_kind='kde')
plt.show()
```

### Регрессионные графики

```python
# Линейная регрессия
plt.figure(figsize=(10, 6))
sns.regplot(data=tips, x='total_bill', y='tip')
plt.title('Линейная регрессия: Чаевые от общего счета')
plt.show()

# Регрессия по категориям
plt.figure(figsize=(12, 6))
sns.lmplot(data=tips, x='total_bill', y='tip', hue='time', height=6)
plt.show()
```

## Сложные компоновки

```python
# Сетка графиков
plt.figure(figsize=(15, 10))

# График 1: Распределение счетов
plt.subplot(2, 3, 1)
sns.histplot(tips['total_bill'], kde=True)
plt.title('Распределение счетов')

# График 2: Средний счет по дням
plt.subplot(2, 3, 2)
sns.barplot(data=tips, x='day', y='total_bill')
plt.title('Средний счет по дням')
plt.xticks(rotation=45)

# График 3: Средний счет по времени
plt.subplot(2, 3, 3)
sns.barplot(data=tips, x='time', y='total_bill')
plt.title('Средний счет по времени')

# График 4: Зависимость чаевых от счета
plt.subplot(2, 3, 4)
sns.scatterplot(data=tips, x='total_bill', y='tip', hue='time')
plt.title('Чаевые vs Счет')

# График 5: Ящик с усами по дням
plt.subplot(2, 3, 5)
sns.boxplot(data=tips, x='day', y='total_bill')
plt.title('Распределение счетов по дням')
plt.xticks(rotation=45)

# График 6: Тепловая карта
plt.subplot(2, 3, 6)
corr_matrix = tips.select_dtypes(include=[np.number]).corr()
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)
plt.title('Корреляции')

plt.tight_layout()
plt.show()
```''',
                'lesson_type': 'lecture',
                'order': 13
            },
            {
                'title': 'Практика: Статистическая визуализация',
                'content': '''# Практическое задание: Статистическая визуализация

Создайте комплексную визуализацию данных о студентах:

1. Создайте DataFrame с данными о студентах:
   - Имя (name)
   - Возраст (age)
   - Оценка (grade)
   - Курс (course)
   - Пол (gender)

2. Постройте распределение оценок с плотностью
3. Создайте ящик с усами для оценок по курсам
4. Постройте столбчатую диаграмму средних оценок по курсам
5. Создайте диаграмму рассеяния возраста и оценок
6. Постройте тепловую карту корреляций
7. Создайте сетку из всех графиков

**Подсказки:**
- Используйте `sns.histplot()` для гистограмм
- Для ящиков с усами используйте `sns.boxplot()`
- Для столбчатых диаграмм используйте `sns.barplot()`
- Для диаграмм рассеяния используйте `sns.scatterplot()`
- Для тепловых карт используйте `sns.heatmap()`
- Используйте `plt.subplot()` для компоновки''',
                'lesson_type': 'practice',
                'order': 14,
                'practice_code_template': '# Статистическая визуализация\nimport seaborn as sns\nimport matplotlib.pyplot as plt\nimport pandas as pd\nimport numpy as np\n\n# 1. Создайте данные о студентах\nnp.random.seed(42)\ndata = {\n    \'name\': [f\'Student_{i}\' for i in range(100)],\n    \'age\': np.random.randint(18, 25, 100),\n    \'grade\': np.random.normal(75, 10, 100),\n    \'course\': np.random.choice([\'Math\', \'Physics\', \'Chemistry\', \'Biology\'], 100),\n    \'gender\': np.random.choice([\'Male\', \'Female\'], 100)\n}\ndf = pd.DataFrame(data)\ndf[\'grade\'] = np.clip(df[\'grade\'], 0, 100)  # Ограничьте оценки от 0 до 100\n\n# 2. Распределение оценок\nplt.figure(figsize=(15, 12))\n\nplt.subplot(2, 3, 1)\n# sns.histplot(df[\'grade\'], kde=True)\n# plt.title(\'Распределение оценок\')\n\n# 3. Ящик с усами по курсам\nplt.subplot(2, 3, 2)\n# sns.boxplot(data=df, x=\'course\', y=\'grade\')\n# plt.title(\'Оценки по курсам\')\n# plt.xticks(rotation=45)\n\n# 4. Средние оценки по курсам\nplt.subplot(2, 3, 3)\n# sns.barplot(data=df, x=\'course\', y=\'grade\')\n# plt.title(\'Средние оценки по курсам\')\n# plt.xticks(rotation=45)\n\n# 5. Диаграмма рассеяния возраста и оценок\nplt.subplot(2, 3, 4)\n# sns.scatterplot(data=df, x=\'age\', y=\'grade\', hue=\'course\')\n# plt.title(\'Возраст vs Оценки\')\n\n# 6. Тепловая карта корреляций\nplt.subplot(2, 3, 5)\n# corr_matrix = df.select_dtypes(include=[np.number]).corr()\n# sns.heatmap(corr_matrix, annot=True, cmap=\'coolwarm\', center=0)\n# plt.title(\'Корреляции\')\n\n# 7. Дополнительный график\nplt.subplot(2, 3, 6)\n# sns.violinplot(data=df, x=\'course\', y=\'grade\')\n# plt.title(\'Распределение оценок по курсам\')\n# plt.xticks(rotation=45)\n\nplt.tight_layout()\nplt.show()'
            },
            {
                'title': 'Временные ряды',
                'content': '''# Временные ряды

Анализ временных рядов — это важный аспект анализа данных, особенно в финансах, экономике и прогнозировании.

## Работа с датами в Pandas

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Создание временного ряда
dates = pd.date_range('2023-01-01', periods=365, freq='D')
values = np.cumsum(np.random.randn(365)) + 100  # Случайное блуждание

ts = pd.Series(values, index=dates)
print(ts.head())

# Установка даты как индекса DataFrame
df = pd.DataFrame({
    'date': pd.date_range('2023-01-01', periods=100, freq='D'),
    'value': np.random.randn(100).cumsum()
})
df.set_index('date', inplace=True)
```

## Ресэмплинг (изменение частоты)

```python
# Ежедневные -> ежемесячные данные
monthly = ts.resample('M').mean()
print(monthly)

# Ежедневные -> недельные данные с агрегацией
weekly_sum = ts.resample('W').sum()
weekly_mean = ts.resample('W').mean()

# Интерполяция пропущенных значений
ts_with_gaps = ts.copy()
ts_with_gaps.iloc[::10] = np.nan  # Добавим пропуски
ts_interpolated = ts_with_gaps.interpolate()
```

## Скользящие окна

```python
# Скользящее среднее
rolling_mean = ts.rolling(window=7).mean()
rolling_std = ts.rolling(window=7).std()

plt.figure(figsize=(12, 6))
plt.plot(ts.index, ts.values, label='Оригинал', alpha=0.7)
plt.plot(rolling_mean.index, rolling_mean.values, label='7-дневное среднее', linewidth=2)
plt.plot(rolling_std.index, rolling_std.values, label='7-дневное отклонение', linewidth=2)
plt.legend()
plt.title('Скользящие средние')
plt.show()
```

## Сезонность и тренды

```python
# Создание данных с трендом и сезонностью
t = np.arange(365)
trend = 0.05 * t  # Линейный тренд
seasonal = 10 * np.sin(2 * np.pi * t / 365.25 * 4)  # Сезонность (4 цикла в году)
noise = np.random.randn(365)  # Шум
signal = trend + seasonal + noise

ts_seasonal = pd.Series(signal, index=pd.date_range('2023-01-01', periods=365, freq='D'))

# Визуализация компонентов
plt.figure(figsize=(15, 10))

plt.subplot(4, 1, 1)
plt.plot(ts_seasonal.index, trend)
plt.title('Тренд')

plt.subplot(4, 1, 2)
plt.plot(ts_seasonal.index, seasonal)
plt.title('Сезонность')

plt.subplot(4, 1, 3)
plt.plot(ts_seasonal.index, noise)
plt.title('Шум')

plt.subplot(4, 1, 4)
plt.plot(ts_seasonal.index, ts_seasonal.values)
plt.title('Полный сигнал')

plt.tight_layout()
plt.show()
```

## Автокорреляция

```python
from pandas.plotting import autocorrelation_plot

# Автокорреляция
plt.figure(figsize=(12, 6))
autocorrelation_plot(ts.iloc[:50])  # Первые 50 точек для наглядности
plt.title('Автокорреляция')
plt.show()

# Лаговые диаграммы
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
lags = [1, 5, 10, 20]

for i, lag in enumerate(lags):
    ax = axes[i//2, i%2]
    ax.scatter(ts.iloc[:-lag], ts.iloc[lag:])
    ax.set_xlabel(f'Значение(t)')
    ax.set_ylabel(f'Значение(t+{lag})')
    ax.set_title(f'Лаг {lag}')

plt.tight_layout()
plt.show()
```''',
                'lesson_type': 'lecture',
                'order': 15
            },
            {
                'title': 'Практика: Анализ временных рядов',
                'content': '''# Практическое задание: Анализ временных рядов

Проанализируйте временной ряд продаж:

1. Создайте временной ряд с данными о продажах за 2 года
2. Добавьте тренд и сезонность к данным
3. Постройте скользящие средние (7, 30, 90 дней)
4. Выполните ресэмплинг до месячных данных
5. Постройте автокорреляцию
6. Создайте лаговые диаграммы

**Подсказки:**
- Используйте `pd.date_range()` для создания диапазона дат
- Для тренда используйте линейную функцию
- Для сезонности используйте синусоидальную функцию
- Для скользящих средних используйте `rolling().mean()`
- Для ресэмплинга используйте `resample()`
- Для автокорреляции используйте `autocorrelation_plot()`''',
                'lesson_type': 'practice',
                'order': 16,
                'practice_code_template': '# Анализ временных рядов\nimport pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\nfrom pandas.plotting import autocorrelation_plot\n\n# 1. Создайте временной ряд продаж за 2 года\ndates = pd.date_range(\'2022-01-01\', periods=730, freq=\'D\')\n\n# 2. Добавьте тренд и сезонность\n# t = np.arange(len(dates))\n# trend = 0.1 * t  # Рост продаж\n# seasonal = 50 * np.sin(2 * np.pi * t / 365.25)  # Годовая сезонность\n# noise = np.random.randn(len(dates)) * 10  # Случайные колебания\n# sales = trend + seasonal + noise + 100\n\n# ts = pd.Series(sales, index=dates)\n# print("Time series head:\\n", ts.head())\n\n# 3. Скользящие средние\n# plt.figure(figsize=(15, 8))\n# plt.plot(ts.index, ts.values, label=\'Оригинал\', alpha=0.7)\n# plt.plot(ts.rolling(7).mean().index, ts.rolling(7).mean().values, label=\'7-дневное среднее\')\n# plt.plot(ts.rolling(30).mean().index, ts.rolling(30).mean().values, label=\'30-дневное среднее\')\n# plt.plot(ts.rolling(90).mean().index, ts.rolling(90).mean().values, label=\'90-дневное среднее\')\n# plt.legend()\n# plt.title(\'Скользящие средние продаж\')\n# plt.show()\n\n# 4. Ресэмплинг до месячных данных\n# monthly_sales = ts.resample(\'M\').sum()\n# print("Monthly sales:\\n", monthly_sales)\n\n# 5. Автокорреляция\n# plt.figure(figsize=(12, 6))\n# autocorrelation_plot(ts.iloc[:100])\n# plt.title(\'Автокорреляция продаж\')\n# plt.show()\n\n# 6. Лаговые диаграммы\n# fig, axes = plt.subplots(1, 3, figsize=(15, 5))\n# lags = [1, 7, 30]\n# for i, lag in enumerate(lags):\n#     axes[i].scatter(ts.iloc[:-lag], ts.iloc[lag:])\n#     axes[i].set_xlabel(f\'Продажи(t)\')\n#     axes[i].set_ylabel(f\'Продажи(t+{lag})\')\n#     axes[i].set_title(f\'Лаг {lag}\')\n# plt.tight_layout()\n# plt.show()'
            },
            {
                'title': 'Введение в машинное обучение',
                'content': '''# Введение в машинное обучение

Машинное обучение (ML) — это область искусственного интеллекта, которая позволяет системам автоматически учиться и улучшаться на основе опыта.

## Типы машинного обучения

### Обучение с учителем (Supervised Learning)
- **Классификация**: предсказание категорий
- **Регрессия**: предсказание числовых значений

### Обучение без учителя (Unsupervised Learning)
- **Кластеризация**: группировка похожих объектов
- **Снижение размерности**: упрощение данных

### Обучение с подкреплением (Reinforcement Learning)
- Обучение через взаимодействие со средой

## Scikit-learn: основы

```python
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, accuracy_score
from sklearn.datasets import load_iris
import pandas as pd
import numpy as np

# Загрузка данных
iris = load_iris()
X, y = iris.data, iris.target

# Разделение на обучающую и тестовую выборки
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Создание и обучение модели
model = LinearRegression()
model.fit(X_train, y_train)

# Предсказания
y_pred = model.predict(X_test)

# Оценка качества
mse = mean_squared_error(y_test, y_pred)
print(f"MSE: {mse}")
```

## Препроцессинг данных

```python
from sklearn.preprocessing import StandardScaler, LabelEncoder

# Масштабирование признаков
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Кодирование категориальных переменных
encoder = LabelEncoder()
categorical_data = ['red', 'blue', 'green', 'red', 'blue']
encoded = encoder.fit_transform(categorical_data)
print(encoded)  # [2, 0, 1, 2, 0]

# Обратное преобразование
original = encoder.inverse_transform(encoded)
print(original)  # ['red', 'blue', 'green', 'red', 'blue']
```

## Кросс-валидация

```python
from sklearn.model_selection import cross_val_score

# Оценка модели с помощью кросс-валидации
scores = cross_val_score(model, X, y, cv=5)
print(f"Средняя точность: {scores.mean():.3f} (+/- {scores.std() * 2:.3f})")
```

## Pipeline: конвейер обработки

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

# Создание pipeline
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('classifier', LogisticRegression())
])

# Обучение pipeline
pipeline.fit(X_train, y_train)

# Предсказания
y_pred = pipeline.predict(X_test)
```

## Выбор модели и гиперпараметры

```python
from sklearn.model_selection import GridSearchCV

# Определение сетки параметров
param_grid = {
    'C': [0.1, 1, 10],
    'penalty': ['l1', 'l2']
}

# Поиск лучших параметров
grid_search = GridSearchCV(
    LogisticRegression(),
    param_grid,
    cv=5,
    scoring='accuracy'
)
grid_search.fit(X_train, y_train)

print(f"Лучшие параметры: {grid_search.best_params_}")
print(f"Лучшая оценка: {grid_search.best_score_}")
```''',
                'lesson_type': 'lecture',
                'order': 17
            },
            {
                'title': 'Практика: Машинное обучение с Scikit-learn',
                'content': '''# Практическое задание: Машинное обучение с Scikit-learn

Создайте модель для предсказания цен на недвижимость:

1. Создайте набор данных о недвижимости:
   - Площадь (area)
   - Количество комнат (rooms)
   - Этаж (floor)
   - Цена (price)

2. Разделите данные на обучающую и тестовую выборки
3. Создайте и обучите линейную регрессию
4. Оцените качество модели с помощью MSE и R²
5. Выполните кросс-валидацию
6. Создайте pipeline с масштабированием

**Подсказки:**
- Используйте `make_regression()` или создайте синтетические данные
- Для разделения используйте `train_test_split()`
- Для линейной регрессии используйте `LinearRegression()`
- Для оценки качества используйте `mean_squared_error()` и `r2_score()`
- Для кросс-валидации используйте `cross_val_score()`
- Для pipeline используйте `Pipeline()`''',
                'lesson_type': 'practice',
                'order': 18,
                'practice_code_template': '# Машинное обучение для недвижимости\nfrom sklearn.model_selection import train_test_split, cross_val_score\nfrom sklearn.linear_model import LinearRegression\nfrom sklearn.metrics import mean_squared_error, r2_score\nfrom sklearn.pipeline import Pipeline\nfrom sklearn.preprocessing import StandardScaler\nimport numpy as np\nimport pandas as pd\n\n# 1. Создайте данные о недвижимости\nnp.random.seed(42)\nn_samples = 1000\narea = np.random.uniform(30, 200, n_samples)\nrooms = np.random.randint(1, 6, n_samples)\nfloor = np.random.randint(1, 20, n_samples)\n# Цена зависит от других признаков + шум\nprice = (area * 1000 + rooms * 5000 + floor * 1000 + \n         np.random.normal(0, 10000, n_samples))\n\nX = np.column_stack([area, rooms, floor])\ny = price\n\n# 2. Разделите на обучающую и тестовую выборки\n# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)\n\n# 3. Создайте и обучите модель\n# model = LinearRegression()\n# model.fit(X_train, y_train)\n\n# 4. Сделайте предсказания\n# y_pred = model.predict(X_test)\n\n# 5. Оцените качество\n# mse = mean_squared_error(y_test, y_pred)\n# r2 = r2_score(y_test, y_pred)\n# print(f"MSE: {mse:.2f}")\n# print(f"R²: {r2:.3f}")\n\n# 6. Кросс-валидация\n# cv_scores = cross_val_score(model, X, y, cv=5)\n# print(f"CV Score: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")\n\n# 7. Pipeline с масштабированием\n# pipeline = Pipeline([\n#     (\'scaler\', StandardScaler()),\n#     (\'regressor\', LinearRegression())\n# ])\n# pipeline.fit(X_train, y_train)\n# y_pred_pipeline = pipeline.predict(X_test)\n# print(f"Pipeline R²: {r2_score(y_test, y_pred_pipeline):.3f}")'
            },
            {
                'title': 'Классификация',
                'content': '''# Классификация

Классификация — это задача машинного обучения, в которой нужно предсказать категорию (класс) объекта.

## Алгоритмы классификации

### Логистическая регрессия

```python
from sklearn.linear_model import LogisticRegression
from sklearn.datasets import make_classification

# Создание синтетических данных
X, y = make_classification(n_samples=1000, n_features=2, n_redundant=0, 
                          n_informative=2, n_clusters_per_class=1, random_state=42)

# Обучение модели
lr = LogisticRegression()
lr.fit(X_train, y_train)

# Предсказания
y_pred = lr.predict(X_test)
y_proba = lr.predict_proba(X_test)  # Вероятности классов
```

### Метод опорных векторов (SVM)

```python
from sklearn.svm import SVC

# SVM с различными ядрами
svm_linear = SVC(kernel='linear')
svm_rbf = SVC(kernel='rbf')
svm_poly = SVC(kernel='poly')

svm_linear.fit(X_train, y_train)
y_pred = svm_linear.predict(X_test)
```

### Деревья решений

```python
from sklearn.tree import DecisionTreeClassifier, plot_tree
import matplotlib.pyplot as plt

# Создание и обучение дерева
dt = DecisionTreeClassifier(max_depth=3, random_state=42)
dt.fit(X_train, y_train)

# Визуализация дерева
plt.figure(figsize=(15, 10))
plot_tree(dt, filled=True, feature_names=['Feature 1', 'Feature 2'], 
          class_names=['Class 0', 'Class 1'])
plt.show()
```

### Случайный лес

```python
from sklearn.ensemble import RandomForestClassifier

# Случайный лес
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)

# Важность признаков
feature_importance = rf.feature_importances_
print("Важность признаков:", feature_importance)
```

## Оценка качества классификации

```python
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve

# Матрица ошибок
cm = confusion_matrix(y_test, y_pred)
print("Матрица ошибок:")
print(cm)

# Подробный отчет
report = classification_report(y_test, y_pred)
print("Отчет классификации:")
print(report)

# ROC-кривая
fpr, tpr, thresholds = roc_curve(y_test, y_proba[:, 1])
auc_score = roc_auc_score(y_test, y_proba[:, 1])

plt.figure(figsize=(8, 6))
plt.plot(fpr, tpr, label=f'ROC Curve (AUC = {auc_score:.3f})')
plt.plot([0, 1], [0, 1], 'k--', label='Random')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve')
plt.legend()
plt.show()
```

## Работа с несбалансированными данными

```python
from sklearn.utils.class_weight import compute_class_weight

# Вычисление весов классов
class_weights = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
class_weight_dict = dict(zip(np.unique(y_train), class_weights))

# Использование весов в модели
lr_balanced = LogisticRegression(class_weight='balanced')
# или
lr_custom = LogisticRegression(class_weight=class_weight_dict)
```''',
                'lesson_type': 'lecture',
                'order': 19
            },
            {
                'title': 'Практика: Классификация заболеваний',
                'content': '''# Практическое задание: Классификация заболеваний

Создайте модель для классификации заболеваний на основе медицинских данных:

1. Создайте набор данных о пациентах:
   - Возраст (age)
   - Пол (gender: 0=женщина, 1=мужчина)
   - Давление (blood_pressure)
   - Холестерин (cholesterol)
   - Заболевание (disease: 0=нет, 1=есть)

2. Разделите данные на обучающую и тестовую выборки
3. Обучите несколько моделей классификации:
   - Логистическую регрессию
   - SVM
   - Дерево решений
   - Случайный лес

4. Оцените качество каждой модели
5. Постройте ROC-кривые для всех моделей
6. Определите лучшую модель

**Подсказки:**
- Используйте `make_classification()` для создания данных
- Для разделения используйте `train_test_split()`
- Для оценки качества используйте `classification_report()` и `confusion_matrix()`
- Для ROC-кривых используйте `roc_curve()` и `roc_auc_score()`
- Сравните AUC-ROC для разных моделей''',
                'lesson_type': 'practice',
                'order': 20,
                'practice_code_template': '# Классификация заболеваний\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.linear_model import LogisticRegression\nfrom sklearn.svm import SVC\nfrom sklearn.tree import DecisionTreeClassifier\nfrom sklearn.ensemble import RandomForestClassifier\nfrom sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve\nimport matplotlib.pyplot as plt\nimport numpy as np\n\n# 1. Создайте данные о пациентах\nnp.random.seed(42)\nn_samples = 1000\nage = np.random.randint(20, 80, n_samples)\ngender = np.random.randint(0, 2, n_samples)\nblood_pressure = np.random.randint(90, 180, n_samples)\ncholesterol = np.random.randint(150, 300, n_samples)\n\n# Заболевание зависит от факторов + шум\nrisk_score = (age * 0.1 + blood_pressure * 0.05 + cholesterol * 0.02 + \n              np.random.normal(0, 5, n_samples))\ndisease = (risk_score > np.percentile(risk_score, 70)).astype(int)\n\nX = np.column_stack([age, gender, blood_pressure, cholesterol])\ny = disease\n\n# 2. Разделите на выборки\n# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)\n\n# 3. Обучите модели\n# models = {\n#     \'Logistic Regression\': LogisticRegression(),\n#     \'SVM\': SVC(probability=True),\n#     \'Decision Tree\': DecisionTreeClassifier(random_state=42),\n#     \'Random Forest\': RandomForestClassifier(random_state=42)\n# }\n\n# results = {}\n# for name, model in models.items():\n#     model.fit(X_train, y_train)\n#     y_pred = model.predict(X_test)\n#     y_proba = model.predict_proba(X_test)[:, 1]\n#     \n#     # Сохраните результаты\n#     results[name] = {\n#         \'predictions\': y_pred,\n#         \'probabilities\': y_proba,\n#         \'auc': roc_auc_score(y_test, y_proba)\n#     }\n\n# 4. Оцените качество лучшей модели\n# best_model_name = max(results.keys(), key=lambda x: results[x][\'auc\'])\n# best_predictions = results[best_model_name][\'predictions\']\n# print(f"Best model: {best_model_name}")\n# print(classification_report(y_test, best_predictions))\n\n# 5. Постройте ROC-кривые\n# plt.figure(figsize=(10, 8))\n# for name, result in results.items():\n#     fpr, tpr, _ = roc_curve(y_test, result[\'probabilities\'])\n#     plt.plot(fpr, tpr, label=f"{name} (AUC = {result[\'auc\']:.3f})")\n# \n# plt.plot([0, 1], [0, 1], \'k--\', label=\'Random\')\n# plt.xlabel(\'False Positive Rate\')\n# plt.ylabel(\'True Positive Rate\')\n# plt.title(\'ROC Curves Comparison\')\n# plt.legend()\n# plt.show()'
            },
            {
                'title': 'Кластеризация',
                'content': '''# Кластеризация

Кластеризация — это задача машинного обучения без учителя, при которой нужно разбить данные на группы (кластеры) похожих объектов.

## Алгоритмы кластеризации

### K-средних (K-Means)

```python
from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs
import matplotlib.pyplot as plt

# Создание синтетических данных
X, _ = make_blobs(n_samples=300, centers=4, cluster_std=0.60, random_state=0)

# K-means с 4 кластерами
kmeans = KMeans(n_clusters=4, random_state=42)
y_kmeans = kmeans.fit_predict(X)

# Центроиды кластеров
centroids = kmeans.cluster_centers_

# Визуализация
plt.figure(figsize=(10, 8))
plt.scatter(X[:, 0], X[:, 1], c=y_kmeans, cmap='viridis', alpha=0.6)
plt.scatter(centroids[:, 0], centroids[:, 1], c='red', s=200, alpha=0.75, marker='X')
plt.title('K-Means Clustering')
plt.show()
```

### Иерархическая кластеризация

```python
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram, linkage

# Иерархическая кластеризация
hierarchical = AgglomerativeClustering(n_clusters=4)
y_hierarchical = hierarchical.fit_predict(X)

# Дендрограмма
plt.figure(figsize=(12, 8))
linkage_matrix = linkage(X, method='ward')
dendrogram(linkage