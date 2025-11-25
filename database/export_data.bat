@echo off
REM Скрипт для экспорта только данных из существующей БД
REM Использование: export_data.bat [host] [port] [user] [database] [output_file]

set HOST=%1
if "%HOST%"=="" set HOST=localhost

set PORT=%2
if "%PORT%"=="" set PORT=5432

set USER=%3
if "%USER%"=="" set USER=forum_owner

set DATABASE=%4
if "%DATABASE%"=="" set DATABASE=forum_database

set OUTPUT_FILE=%5
if "%OUTPUT_FILE%"=="" set OUTPUT_FILE=data_only.sql

echo ==========================================
echo Экспорт данных из базы данных
echo ==========================================
echo Хост: %HOST%:%PORT%
echo База данных: %DATABASE%
echo Пользователь: %USER%
echo Выходной файл: %OUTPUT_FILE%
echo.

REM Устанавливаем пароль
set PGPASSWORD=1111

REM Экспортируем только данные (без схемы)
pg_dump -h %HOST% -p %PORT% -U %USER% -d %DATABASE% --data-only --no-owner --no-acl --inserts -f %OUTPUT_FILE%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Данные успешно экспортированы в %OUTPUT_FILE%
    for %%A in (%OUTPUT_FILE%) do echo Размер файла: %%~zA байт
) else (
    echo.
    echo ❌ Ошибка при экспорте данных
    exit /b 1
)

pause

