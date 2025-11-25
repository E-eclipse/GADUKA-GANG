# Быстрая загрузка данных из существующего бэкапа (PowerShell)
# Использование: .\quick_load.ps1 [backup_file.sql]

param(
    [Parameter(Mandatory=$true)]
    [string]$BackupFile
)

if (-not (Test-Path $BackupFile)) {
    Write-Host "❌ Файл $BackupFile не найден!" -ForegroundColor Red
    exit 1
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Быстрая загрузка данных из бэкапа" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Файл: $BackupFile"
Write-Host ""

$containerName = "gadukagang-postgres"

# Проверяем, запущен ли контейнер
$containerRunning = docker ps --filter "name=$containerName" --format "{{.Names}}" | Select-String -Pattern $containerName
if (-not $containerRunning) {
    Write-Host "⚠️  Контейнер не запущен. Запускаю..." -ForegroundColor Yellow
    docker-compose up -d postgres
    Write-Host "Ожидание готовности БД..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
}

Write-Host "Загружаю данные..." -ForegroundColor Yellow
try {
    Get-Content $BackupFile | docker exec -i $containerName psql -U forum_owner -d forum_database
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Данные успешно загружены!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Проверка данных:" -ForegroundColor Cyan
        docker exec -it $containerName psql -U forum_owner -d forum_database -c "SELECT COUNT(*) as users FROM users; SELECT COUNT(*) as posts FROM posts; SELECT COUNT(*) as topics FROM topics;"
    } else {
        Write-Host ""
        Write-Host "❌ Ошибка при загрузке данных" -ForegroundColor Red
        Write-Host "Проверьте логи: docker logs $containerName" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "❌ Ошибка: $_" -ForegroundColor Red
    exit 1
}

