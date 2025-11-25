# Скрипт для экспорта только данных из существующей БД (PowerShell)
# Использование: .\export_data.ps1 [host] [port] [user] [database] [output_file]

param(
    [string]$Host = "localhost",
    [int]$Port = 5432,
    [string]$User = "forum_owner",
    [string]$Database = "forum_database",
    [string]$OutputFile = "data_only.sql"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Экспорт данных из базы данных" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Хост: $Host`:$Port"
Write-Host "База данных: $Database"
Write-Host "Пользователь: $User"
Write-Host "Выходной файл: $OutputFile"
Write-Host ""

# Проверяем наличие pg_dump
$pgDumpPath = Get-Command pg_dump -ErrorAction SilentlyContinue
if (-not $pgDumpPath) {
    Write-Host "❌ pg_dump не найден в PATH!" -ForegroundColor Red
    Write-Host "Убедитесь, что PostgreSQL установлен и добавлен в PATH" -ForegroundColor Yellow
    exit 1
}

# Устанавливаем переменную окружения для пароля
$env:PGPASSWORD = "1111"

# Формируем команду
$pgDumpArgs = @(
    "-h", $Host,
    "-p", $Port.ToString(),
    "-U", $User,
    "-d", $Database,
    "--data-only",
    "--no-owner",
    "--no-acl",
    "--inserts",
    "-f", $OutputFile
)

Write-Host "Выполняю экспорт данных..." -ForegroundColor Yellow
try {
    & pg_dump $pgDumpArgs
    
    if ($LASTEXITCODE -eq 0) {
        $fileSize = (Get-Item $OutputFile).Length / 1MB
        Write-Host ""
        Write-Host "✅ Данные успешно экспортированы в $OutputFile" -ForegroundColor Green
        Write-Host "Размер файла: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "❌ Ошибка при экспорте данных" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "❌ Ошибка: $_" -ForegroundColor Red
    exit 1
} finally {
    # Очищаем пароль из переменных окружения
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
}

