"""
Django management команда для восстановления БД из бэкапа
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess
import os
import gzip


class Command(BaseCommand):
    help = 'Восстанавливает базу данных из резервной копии'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Путь к файлу бэкапа'
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Подтвердить восстановление (ВНИМАНИЕ: текущие данные будут удалены!)'
        )

    def handle(self, *args, **options):
        backup_file = options['file']
        confirm = options.get('confirm', False)
        
        if not os.path.exists(backup_file):
            self.stdout.write(self.style.ERROR(f'Файл не найден: {backup_file}'))
            return
        
        # Получаем настройки БД
        db_settings = settings.DATABASES['default']
        db_name = db_settings['NAME']
        db_user = db_settings['USER']
        db_password = db_settings.get('PASSWORD', '')
        db_host = db_settings.get('HOST', 'localhost')
        db_port = db_settings.get('PORT', '5432')
        
        self.stdout.write(self.style.WARNING(f'\n⚠️  ВОССТАНОВЛЕНИЕ БАЗЫ ДАННЫХ'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'  База данных: {db_name}')
        self.stdout.write(f'  Хост: {db_host}:{db_port}')
        self.stdout.write(f'  Файл бэкапа: {backup_file}')
        self.stdout.write('')
        self.stdout.write(self.style.ERROR('  ⚠️  ВСЕ ТЕКУЩИЕ ДАННЫЕ БУДУТ УДАЛЕНЫ!'))
        self.stdout.write('')
        
        if not confirm:
            self.stdout.write(self.style.ERROR('❌ Для подтверждения используйте флаг --confirm'))
            return
        
        try:
            env = os.environ.copy()
            if db_password:
                env['PGPASSWORD'] = db_password
            
            # Проверяем, сжат ли файл
            is_compressed = backup_file.endswith('.gz')
            
            # Формируем команду psql
            cmd = [
                'psql',
                '-h', db_host,
                '-p', str(db_port),
                '-U', db_user,
                '-d', db_name,
                '-q'  # Quiet mode
            ]
            
            self.stdout.write('🔄 Восстановление данных...')
            
            if is_compressed:
                # Распаковываем и передаём в psql
                with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                    result = subprocess.run(
                        cmd,
                        stdin=f,
                        stderr=subprocess.PIPE,
                        env=env,
                        text=True
                    )
            else:
                # Читаем обычный файл
                with open(backup_file, 'r', encoding='utf-8') as f:
                    result = subprocess.run(
                        cmd,
                        stdin=f,
                        stderr=subprocess.PIPE,
                        env=env,
                        text=True
                    )
            
            if result.returncode != 0:
                self.stdout.write(self.style.WARNING(f'Предупреждения: {result.stderr}'))
            
            self.stdout.write(self.style.SUCCESS('\n✅ База данных восстановлена успешно!'))
            self.stdout.write('\n⚠️  Рекомендуется перезапустить сервер Django')
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('\n❌ psql не найден!'))
            self.stdout.write('Убедитесь, что PostgreSQL установлен и psql доступен в PATH')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Ошибка восстановления: {e}'))
            raise
