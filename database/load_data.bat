@echo off
REM Скрипт для загрузки данных в Docker контейнер
REM Использование: load_data.bat [data_file.sql] [container_name]

set DATA_FILE=%1
if "%DATA_FILE%"=="" set DATA_FILE=data_only.sql

set CONTAINER_NAME=%2
if "%CONTAINER_NAME%"=="" set CONTAINER_NAME=gadukagang-postgres

if not exist "%DATA_FILE%" (
    echo ❌ Файл %DATA_FILE% не найден!
    pause
    exit /b 1
)

echo ==========================================
echo Загрузка данных в Docker контейнер
echo ==========================================
echo Файл данных: %DATA_FILE%
echo Контейнер: %CONTAINER_NAME%
echo.

REM Проверяем, запущен ли контейнер
docker ps | findstr "%CONTAINER_NAME%" >nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Контейнер %CONTAINER_NAME% не запущен!
    echo Запустите контейнер командой: docker-compose up -d
    pause
    exit /b 1
)

echo Загружаем данные в базу...
type "%DATA_FILE%" | docker exec -i "%CONTAINER_NAME%" psql -U forum_owner -d forum_database

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Данные успешно загружены!
    echo.
    echo Проверка данных:
    docker exec "%CONTAINER_NAME%" psql -U forum_owner -d forum_database -c "SELECT COUNT(*) as users FROM users; SELECT COUNT(*) as posts FROM posts; SELECT COUNT(*) as topics FROM topics;"
) else (
    echo.
    echo ❌ Ошибка при загрузке данных
    echo Проверьте логи: docker logs %CONTAINER_NAME%
    pause
    exit /b 1
)

pause

