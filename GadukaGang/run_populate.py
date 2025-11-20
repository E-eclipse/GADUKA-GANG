import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GadukaGang.settings')
django.setup()

# Импорт моделей и заполнение данными
from GadukaGang.models import PracticeTopic, PracticeLevel

# Создаем темы практики
python_basics_topic, created = PracticeTopic.objects.get_or_create(
    name='Основы Python',
    defaults={
        'description': 'Изучение основ программирования на Python',
        'order': 1,
        'is_active': True
    }
)

data_structures_topic, created = PracticeTopic.objects.get_or_create(
    name='Структуры данных',
    defaults={
        'description': 'Изучение основных структур данных в Python',
        'order': 2,
        'is_active': True
    }
)

# Создаем уровни для темы "Основы Python"
level1_theory_questions = [
    {
        'question': 'Что такое переменная в Python?',
        'options': [
            {'value': 'a', 'text': 'Объект, который хранит данные'},
            {'value': 'b', 'text': 'Команда для выполнения операций'},
            {'value': 'c', 'text': 'Специальный тип данных'},
            {'value': 'd', 'text': 'Ничто из вышеперечисленного'}
        ],
        'correct_answer': 'a'
    },
    {
        'question': 'Какой тип данных используется для хранения целых чисел?',
        'options': [
            {'value': 'a', 'text': 'float'},
            {'value': 'b', 'text': 'int'},
            {'value': 'c', 'text': 'str'},
            {'value': 'd', 'text': 'bool'}
        ],
        'correct_answer': 'b'
    }
]

level1_test_cases = [
    {
        'input': '2\n3',
        'output': '5'
    },
    {
        'input': '10\n20',
        'output': '30'
    }
]

level1, created = PracticeLevel.objects.get_or_create(
    topic=python_basics_topic,
    name='Переменные и типы данных',
    defaults={
        'description': 'Изучение переменных и базовых типов данных в Python',
        'difficulty': 'beginner',
        'order': 1,
        'theory_content': 'Переменная в Python - это имя, которое ссылается на значение. Переменные создаются при первом присваивании значения.\n\nОсновные типы данных:\n- int (целые числа)\n- float (вещественные числа)\n- str (строки)\n- bool (логический тип)',
        'task_description': 'Напишите программу, которая считывает два целых числа с клавиатуры и выводит их сумму.',
        'solution_template': '# Введите ваше решение здесь\na = int(input())\nb = int(input())\nprint(a + b)',
        'theory_questions': level1_theory_questions,
        'test_cases': level1_test_cases
    }
)

level2_theory_questions = [
    {
        'question': 'Что такое условный оператор?',
        'options': [
            {'value': 'a', 'text': 'Оператор, который выполняет код в зависимости от условия'},
            {'value': 'b', 'text': 'Оператор для создания циклов'},
            {'value': 'c', 'text': 'Оператор для объявления функций'},
            {'value': 'd', 'text': 'Оператор для работы с массивами'}
        ],
        'correct_answer': 'a'
    },
    {
        'question': 'Какой оператор используется для проверки равенства?',
        'options': [
            {'value': 'a', 'text': '='},
            {'value': 'b', 'text': '=='},
            {'value': 'c', 'text': '==='},
            {'value': 'd', 'text': '!='}
        ],
        'correct_answer': 'b'
    }
]

level2_test_cases = [
    {
        'input': '5\n3',
        'output': '5 больше'
    },
    {
        'input': '2\n7',
        'output': '7 больше'
    },
    {
        'input': '4\n4',
        'output': 'Числа равны'
    }
]

level2, created = PracticeLevel.objects.get_or_create(
    topic=python_basics_topic,
    name='Условные операторы',
    defaults={
        'description': 'Изучение условных операторов if, elif, else',
        'difficulty': 'beginner',
        'order': 2,
        'theory_content': 'Условные операторы позволяют выполнять разные блоки кода в зависимости от выполнения условий.\n\nСинтаксис:\nif условие:\n    блок кода\nelif другое_условие:\n    другой блок кода\nelse:\n    блок кода, если ни одно условие не выполнено',
        'task_description': 'Напишите программу, которая считывает два целых числа и выводит, какое из них больше, или "Числа равны", если они равны.',
        'solution_template': '# Введите ваше решение здесь\na = int(input())\nb = int(input())\nif a > b:\n    print(f"{a} больше")\nelif b > a:\n    print(f"{b} больше")\nelse:\n    print("Числа равны")',
        'theory_questions': level2_theory_questions,
        'test_cases': level2_test_cases
    }
)

# Создаем уровни для темы "Структуры данных"
level3_theory_questions = [
    {
        'question': 'Что такое список в Python?',
        'options': [
            {'value': 'a', 'text': 'Упорядоченная коллекция элементов'},
            {'value': 'b', 'text': 'Неизменяемая коллекция элементов'},
            {'value': 'c', 'text': 'Коллекция уникальных элементов'},
            {'value': 'd', 'text': 'Коллекция пар ключ-значение'}
        ],
        'correct_answer': 'a'
    }
]

level3_test_cases = [
    {
        'input': '3\n1\n2\n3',
        'output': '6'
    },
    {
        'input': '5\n10\n20\n30\n40\n50',
        'output': '150'
    }
]

level3, created = PracticeLevel.objects.get_or_create(
    topic=data_structures_topic,
    name='Списки',
    defaults={
        'description': 'Изучение списков в Python',
        'difficulty': 'intermediate',
        'order': 1,
        'theory_content': 'Список в Python - это упорядоченная изменяемая коллекция элементов.\n\nСоздание списка:\nmy_list = [1, 2, 3]\n\nОсновные операции:\n- Добавление элемента: append()\n- Удаление элемента: remove()\n- Доступ по индексу: my_list[0]',
        'task_description': 'Напишите программу, которая считывает количество чисел N, затем N чисел, и выводит их сумму.',
        'solution_template': '# Введите ваше решение здесь\nn = int(input())\nnumbers = []\nfor i in range(n):\n    number = int(input())\n    numbers.append(number)\nprint(sum(numbers))',
        'theory_questions': level3_theory_questions,
        'test_cases': level3_test_cases
    }
)

print("Успешно заполнены примеры заданий по практике")