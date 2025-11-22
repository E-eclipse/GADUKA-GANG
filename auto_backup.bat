@echo off
REM Скрипт автоматического резервного копирования БД
REM Запускать через планировщик задач Windows

echo ========================================
echo Автоматическое резервное копирование БД
echo ========================================
echo.

REM Переход в директорию проекта
cd /d "c:\Users\Mathew\Desktop\техникум\4-й курс\Gaduka Gang\GadukaGang"

REM Создание бэкапа с сжатием
echo Создание резервной копии...
python manage.py backup_db --output=backups --compress

REM Удаление старых бэкапов (старше 30 дней)
echo.
echo Очистка старых бэкапов...
forfiles /P backups /M *.sql.gz /D -30 /C "cmd /c del @path" 2>nul

echo.
echo ========================================
echo Резервное копирование завершено!
echo ========================================
echo.

REM Логирование
echo [%date% %time%] Backup completed >> backups\backup.log

pause
