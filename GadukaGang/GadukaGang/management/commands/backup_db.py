"""
Django management команда для создания резервной копии БД
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess
import os
from datetime import datetime


class Command(BaseCommand):
    help = 'Создаёт резервную копию базы данных PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='backups',
            help='Директория для сохранения бэкапов'
        )
        parser.add_argument(
            '--compress',
            action='store_true',
            help='Сжать бэкап с помощью gzip'
        )

    def handle(self, *args, **options):
        output_dir = options['output']
        compress = options.get('compress', False)
        
        # Создаём директорию если не существует
        os.makedirs(output_dir, exist_ok=True)
        
        # Получаем настройки БД
        db_settings = settings.DATABASES['default']
        db_name = db_settings['NAME']
        db_user = db_settings['USER']
        db_password = db_settings.get('PASSWORD', '')
        db_host = db_settings.get('HOST', 'localhost')
        db_port = db_settings.get('PORT', '5432')
        
        # Формируем имя файла
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'backup_{db_name}_{timestamp}.sql'
        if compress:
            filename += '.gz'
        
        filepath = os.path.join(output_dir, filename)
        
        self.stdout.write(self.style.SUCCESS(f'\n💾 Создание резервной копии БД'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'  База данных: {db_name}')
        self.stdout.write(f'  Хост: {db_host}:{db_port}')
        self.stdout.write(f'  Файл: {filepath}')
        self.stdout.write('')
        
        try:
            # Формируем команду pg_dump
            env = os.environ.copy()
            if db_password:
                env['PGPASSWORD'] = db_password
            
            cmd = [
                'pg_dump',
                '-h', db_host,
                '-p', str(db_port),
                '-U', db_user,
                '-F', 'p',  # Plain text format
                '--no-owner',
                '--no-acl',
                db_name
            ]
            
            # Выполняем бэкап
            with open(filepath if not compress else filepath[:-3], 'w', encoding='utf-8') as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True
                )
            
            if result.returncode != 0:
                raise Exception(f'pg_dump завершился с ошибкой: {result.stderr}')
            
            # Сжимаем если нужно
            if compress:
                import gzip
                import shutil
                with open(filepath[:-3], 'rb') as f_in:
                    with gzip.open(filepath, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(filepath[:-3])
            
            # Получаем размер файла
            file_size = os.path.getsize(filepath)
            size_mb = file_size / (1024 * 1024)
            
            self.stdout.write(self.style.SUCCESS(f'✅ Бэкап создан успешно!'))
            self.stdout.write(f'  Размер: {size_mb:.2f} MB')
            self.stdout.write(f'  Путь: {filepath}')
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('\n❌ pg_dump не найден!'))
            self.stdout.write('Убедитесь, что PostgreSQL установлен и pg_dump доступен в PATH')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Ошибка создания бэкапа: {e}'))
            raise
