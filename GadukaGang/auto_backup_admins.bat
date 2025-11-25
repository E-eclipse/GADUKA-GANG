@echo off
REM Скрипт автоматической отправки бекапов БД админам
REM Запускать через планировщик задач Windows каждые 3 часа

echo ========================================
echo Автоматическая отправка бекапов админам
echo ========================================
echo.

REM Переход в директорию проекта
cd /d "C:\Users\Mathew\Desktop\техникум\4-й курс\Gaduka Gang\GadukaGang"

REM Создание и отправка бекапа
echo Создание резервной копии и отправка админам...
python manage.py send_backup_to_admins --compress

echo.
echo ========================================
echo Отправка бекапов завершена!
echo ========================================
echo.

REM Логирование
echo [%date% %time%] Backup sent to admins >> backups\backup.log

