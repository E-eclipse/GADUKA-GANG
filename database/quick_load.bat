@echo off
REM Быстрая загрузка данных из существующего бэкапа
REM Использование: quick_load.bat [backup_file.sql]

set BACKUP_FILE=%1
if "%BACKUP_FILE%"=="" (
    echo Использование: quick_load.bat [backup_file.sql]
    echo Пример: quick_load.bat ..\GadukaGang\backups\backup_20251122_191754.sql
    pause
    exit /b 1
)

if not exist "%BACKUP_FILE%" (
    echo ❌ Файл %BACKUP_FILE% не найден!
    pause
    exit /b 1
)

echo ==========================================
echo Быстрая загрузка данных из бэкапа
echo ==========================================
echo Файл: %BACKUP_FILE%
echo.

REM Проверяем, запущен ли контейнер
docker ps | findstr "gadukagang-postgres" >nul
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️  Контейнер не запущен. Запускаю...
    docker-compose up -d postgres
    echo Ожидание готовности БД...
    timeout /t 10 /nobreak >nul
)

echo Загружаю данные...
type "%BACKUP_FILE%" | docker exec -i gadukagang-postgres psql -U forum_owner -d forum_database

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Данные успешно загружены!
    echo.
    echo Проверка данных:
    docker exec -it gadukagang-postgres psql -U forum_owner -d forum_database -c "SELECT COUNT(*) as users FROM users; SELECT COUNT(*) as posts FROM posts; SELECT COUNT(*) as topics FROM topics;"
) else (
    echo.
    echo ❌ Ошибка при загрузке данных
    echo Проверьте логи: docker logs gadukagang-postgres
)

pause

