"""
Views for data management (CSV import/export, database backups)
"""
import os
import csv
import gzip
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, JsonResponse, FileResponse
from django.conf import settings
from django.db import connection
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from .models import User, Section, Topic, Post, Tag, Achievement, UserRank
from .management.commands.export_csv import Command as ExportCommand


@staff_member_required
def csv_operations_view(request):
    """Main page for CSV import/export operations"""
    return render(request, 'data_management/csv_operations.html', {
        'entity_types': [
            {'value': 'users', 'label': 'Пользователи'},
            {'value': 'sections', 'label': 'Разделы'},
            {'value': 'topics', 'label': 'Темы'},
            {'value': 'posts', 'label': 'Сообщения'},
            {'value': 'tags', 'label': 'Теги'},
            {'value': 'achievements',  'label': 'Достижения'},
            {'value': 'ranks', 'label': 'Ранги'},
        ]
    })


@staff_member_required
def handle_csv_import(request):
    """Handle CSV file upload and import"""
    if request.method != 'POST':
        return redirect('csv_operations')
    
    entity_type = request.POST.get('entity_type')
    skip_errors = request.POST.get('skip_errors') == 'on'
    csv_file = request.FILES.get('csv_file')
    
    if not csv_file:
        messages.error(request, 'Файл не выбран')
        return redirect('csv_operations')
    
    if not csv_file.name.endswith('.csv'):
        messages.error(request, 'Файл должен быть в формате CSV')
        return redirect('csv_operations')
    
    # Save uploaded file temporarily
    temp_path = default_storage.save(f'temp/{csv_file.name}', ContentFile(csv_file.read()))
    full_temp_path = os.path.join(settings.MEDIA_ROOT, temp_path)
    
    try:
        from .management.commands.import_csv import Command as ImportCommand
        import_cmd = ImportCommand()
        
        # Call the appropriate import method
        if entity_type == 'users':
            import_cmd.import_users(full_temp_path, skip_errors)
        elif entity_type == 'sections':
            import_cmd.import_sections(full_temp_path, skip_errors)
        elif entity_type == 'topics':
            import_cmd.import_topics(full_temp_path, skip_errors)
        elif entity_type == 'posts':
            import_cmd.import_posts(full_temp_path, skip_errors)
        elif entity_type == 'tags':
            import_cmd.import_tags(full_temp_path, skip_errors)
        elif entity_type == 'achievements':
            import_cmd.import_achievements(full_temp_path, skip_errors)
        elif entity_type == 'ranks':
            import_cmd.import_ranks(full_temp_path, skip_errors)
        
        # Clean up temp file
        default_storage.delete(temp_path)
        
        messages.success(request, f'✅ Импорт завершён успешно!')
        
    except Exception as e:
        messages.error(request, f'Ошибка импорта: {str(e)}')
        if default_storage.exists(temp_path):
            default_storage.delete(temp_path)
    
    return redirect('csv_operations')


@staff_member_required
def download_csv_export(request, entity_type):
    """Generate and download CSV export"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_exports')
        os.makedirs(temp_dir, exist_ok=True)
        
        export_cmd = ExportCommand()
        
        if entity_type == 'all':
            # Export all entities
            for entity in ['users', 'sections', 'topics', 'posts', 'tags', 'achievements', 'ranks']:
                method = getattr(export_cmd, f'export_{entity}')
                method(temp_dir, timestamp)
            filename = f'users_{timestamp}.csv'
        else:
            # Export single entity
            filename = f'{entity_type}_{timestamp}.csv'
            method = getattr(export_cmd, f'export_{entity_type}', None)
            if method:
                method(temp_dir, timestamp)
            else:
                messages.error(request, f'Неизвестный тип данных: {entity_type}')
                return redirect('csv_operations')
        
        file_path = os.path.join(temp_dir, filename)
        
        if os.path.exists(file_path):
            response = FileResponse(open(file_path, 'rb'), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            messages.error(request, f'Файл экспорта не найден: {filename}')
            return redirect('csv_operations')
            
    except Exception as e:
        messages.error(request, f'Ошибка экспорта: {str(e)}')
        return redirect('csv_operations')


@staff_member_required
def backup_management_view(request):
    """Page for database backup management"""
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    backups = []
    for filename in os.listdir(backup_dir):
        if filename.endswith('.sql') or filename.endswith('.sql.gz'):
            filepath = os.path.join(backup_dir, filename)
            stat = os.stat(filepath)
            backups.append({
                'filename': filename,
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created': datetime.fromtimestamp(stat.st_mtime),
                'compressed': filename.endswith('.gz')
            })
    
    backups.sort(key=lambda x: x['created'], reverse=True)
    
    return render(request, 'data_management/backup_management.html', {
        'backups': backups,
        'backup_dir': backup_dir
    })


@staff_member_required
def create_backup(request):
    """Create new database backup"""
    if request.method != 'POST':
        return redirect('backup_management')
    
    compress = request.POST.get('compress') == 'on'
    
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        filename = f'backup_{timestamp}.sql'
        if compress:
            filename += '.gz'
        
        backup_path = os.path.join(backup_dir, filename)
        db_settings = settings.DATABASES['default']
        
        dump_cmd = [
            'pg_dump',
            '-h', db_settings['HOST'],
            '-p', str(db_settings['PORT']),
            '-U', db_settings['USER'],
            '-d', db_settings['NAME'],
            '-F', 'p',
            '--no-owner',
            '--no-acl',
        ]
        
        import subprocess
        env = os.environ.copy()
        env['PGPASSWORD'] = db_settings['PASSWORD']
        
        if compress:
            with open(backup_path, 'wb') as f:
                dump_process = subprocess.Popen(dump_cmd, stdout=subprocess.PIPE, env=env)
                gzip_process = subprocess.Popen(['gzip'], stdin=dump_process.stdout, stdout=f)
                dump_process.stdout.close()
                gzip_process.communicate()
        else:
            with open(backup_path, 'w') as f:
                subprocess.run(dump_cmd, stdout=f, env=env, check=True)
        
        messages.success(request, f'✅ Бэкап успешно создан: {filename}')
        
    except Exception as e:
        messages.error(request, f'Ошибка создания бэкапа: {str(e)}')
    
    return redirect('backup_management')


@staff_member_required
def delete_backup(request, filename):
    """Delete backup file"""
    if request.method != 'POST':
        return redirect('backup_management')
    
    try:
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        backup_path = os.path.join(backup_dir, filename)
        
        if os.path.exists(backup_path):
            os.remove(backup_path)
            messages.success(request, f'✅ Бэкап удалён: {filename}')
        else:
            messages.error(request, f'Файл не найден: {filename}')
            
    except Exception as e:
        messages.error(request, f'Ошибка удаления: {str(e)}')
    
    return redirect('backup_management')


@staff_member_required
def download_backup(request, filename):
    """Download backup file"""
    try:
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        backup_path = os.path.join(backup_dir, filename)
        
        if os.path.exists(backup_path):
            response = FileResponse(open(backup_path, 'rb'))
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            messages.error(request, f'Файл не найден: {filename}')
            return redirect('backup_management')
            
    except Exception as e:
        messages.error(request, f'Ошибка скачивания: {str(e)}')
        return redirect('backup_management')
