"""
Django management команда для создания резервной копии БД и отправки её админам
"""
from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib.auth import get_user_model
import subprocess
import os
from datetime import datetime
import gzip
import shutil

User = get_user_model()


class Command(BaseCommand):
    help = 'Создаёт резервную копию БД и отправляет её всем админам на email'

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
            default=True,
            help='Сжать бэкап с помощью gzip'
        )
        parser.add_argument(
            '--keep-file',
            action='store_true',
            help='Не удалять файл после отправки'
        )

    def handle(self, *args, **options):
        output_dir = options['output']
        compress = options.get('compress', True)
        keep_file = options.get('keep_file', False)
        
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
        
        self.stdout.write(self.style.SUCCESS(f'\n💾 Создание резервной копии БД для отправки админам'))
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
            temp_filepath = filepath if not compress else filepath[:-3]
            with open(temp_filepath, 'w', encoding='utf-8') as f:
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
                with open(temp_filepath, 'rb') as f_in:
                    with gzip.open(filepath, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(temp_filepath)
            
            # Получаем размер файла
            file_size = os.path.getsize(filepath)
            size_mb = file_size / (1024 * 1024)
            
            self.stdout.write(self.style.SUCCESS(f'✅ Бэкап создан успешно!'))
            self.stdout.write(f'  Размер: {size_mb:.2f} MB')
            self.stdout.write(f'  Путь: {filepath}')
            
            # Получаем всех админов с email
            admin_roles = ['admin_level_1', 'admin_level_2', 'admin_level_3', 'super_admin']
            admins = User.objects.filter(
                role__in=admin_roles,
                is_active=True,
                email__isnull=False
            ).exclude(email='').distinct()
            
            # Также включаем superuser и staff
            superusers = User.objects.filter(
                is_superuser=True,
                is_active=True,
                email__isnull=False
            ).exclude(email='').distinct()
            
            # Объединяем списки
            all_admins = list(admins) + [u for u in superusers if u not in admins]
            
            if not all_admins:
                self.stdout.write(self.style.WARNING('⚠️  Не найдено админов с email для отправки'))
                if not keep_file:
                    os.remove(filepath)
                return
            
            admin_emails = [admin.email for admin in all_admins if admin.email]
            
            self.stdout.write(f'\n📧 Отправка бекапа {len(admin_emails)} админам...')
            
            # Отправляем email каждому админу
            success_count = 0
            for admin_email in admin_emails:
                try:
                    email = EmailMessage(
                        subject=f'Резервная копия БД Gaduka Gang - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                        body=f'''
Здравствуйте!

Это автоматическая отправка резервной копии базы данных Gaduka Gang Forum.

Детали бекапа:
- Дата создания: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- Размер файла: {size_mb:.2f} MB
- База данных: {db_name}
- Сжатие: {'Да (gzip)' if compress else 'Нет'}

Файл прикреплен к письму.

---
Это автоматическое сообщение от системы резервного копирования.
''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[admin_email],
                    )
                    
                    # Прикрепляем файл
                    with open(filepath, 'rb') as f:
                        email.attach(filename, f.read(), 'application/gzip' if compress else 'application/sql')
                    
                    email.send()
                    success_count += 1
                    self.stdout.write(f'  ✅ Отправлено: {admin_email}')
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ❌ Ошибка отправки на {admin_email}: {str(e)}'))
            
            self.stdout.write(self.style.SUCCESS(f'\n✅ Успешно отправлено {success_count} из {len(admin_emails)} писем'))
            
            # Удаляем файл если не нужно его сохранять
            if not keep_file:
                os.remove(filepath)
                self.stdout.write(f'🗑️  Временный файл удален')
            else:
                self.stdout.write(f'💾 Файл сохранен: {filepath}')
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('\n❌ pg_dump не найден!'))
            self.stdout.write('Убедитесь, что PostgreSQL установлен и pg_dump доступен в PATH')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Ошибка: {e}'))
            raise

