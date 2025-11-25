#!/usr/bin/env python
"""Скрипт для применения миграции"""
import os
import sys
import django

# Добавляем путь к проекту
project_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'GadukaGang')
sys.path.insert(0, project_dir)

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GadukaGang.settings')
django.setup()

from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.chdir(project_dir)
    execute_from_command_line(['manage.py', 'migrate'])

