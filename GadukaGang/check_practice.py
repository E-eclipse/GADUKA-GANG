import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GadukaGang.settings')
django.setup()

# Импорт моделей
from GadukaGang.models import PracticeTopic, PracticeLevel

print("Проверка тем практики:")
topics = PracticeTopic.objects.all()
for topic in topics:
    print(f"- {topic.name}: {topic.description}")
    
    levels = PracticeLevel.objects.filter(topic=topic)
    for level in levels:
        print(f"  * {level.name}: {level.description}")
        print(f"    Теория: {level.theory_content[:50]}...")
        print(f"    Задание: {level.task_description[:50]}...")
        print(f"    Вопросы: {len(level.theory_questions)}")
        print(f"    Тесты: {len(level.test_cases)}")
        print()

print(f"Всего тем: {topics.count()}")
print(f"Всего уровней: {PracticeLevel.objects.count()}")