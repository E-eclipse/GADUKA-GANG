#!/usr/bin/env python
"""Скрипт для применения миграции через Django"""
import os
import django

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GadukaGang.settings')
django.setup()

from django.core.management import call_command

if __name__ == '__main__':
    print("Применение миграций...")
    call_command('migrate', verbosity=2)
    print("Миграции применены успешно!")

