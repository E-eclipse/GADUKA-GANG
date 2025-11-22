"""
Django management команда для применения SQL процедур, триггеров и VIEW
"""
from django.core.management.base import BaseCommand
from django.db import connection
import os


class Command(BaseCommand):
    help = 'Применяет SQL процедуры, триггеры и VIEW из файлов database/'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['procedures', 'triggers', 'views', 'all'],
            default='all',
            help='Тип SQL объектов для применения'
        )

    def handle(self, *args, **options):
        sql_type = options['type']
        
        # Определяем базовый путь к SQL файлам
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        database_dir = os.path.join(base_dir, '..', 'database')
        
        files_to_execute = []
        
        if sql_type in ['procedures', 'all']:
            files_to_execute.append(('procedures.sql', 'Процедуры'))
        if sql_type in ['triggers', 'all']:
            files_to_execute.append(('triggers.sql', 'Триггеры'))
        if sql_type in ['views', 'all']:
            files_to_execute.append(('views.sql', 'Представления'))
        
        with connection.cursor() as cursor:
            for filename, description in files_to_execute:
                filepath = os.path.join(database_dir, filename)
                
                if not os.path.exists(filepath):
                    self.stdout.write(
                        self.style.WARNING(f'Файл {filename} не найден: {filepath}')
                    )
                    continue
                
                self.stdout.write(f'Применение {description} из {filename}...')
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        sql = f.read()
                    
                    # Выполняем SQL
                    cursor.execute(sql)
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ {description} успешно применены')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Ошибка при применении {description}: {str(e)}')
                    )
        
        self.stdout.write(self.style.SUCCESS('\nГотово!'))
