# Скрипт для загрузки данных в Docker контейнер (PowerShell)
# Использование: .\load_data.ps1 [data_file.sql] [container_name]

param(
    [string]$DataFile = "data_only.sql",
    [string]$ContainerName = "gadukagang-postgres"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Загрузка данных в Docker контейнер" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Файл данных: $DataFile"
Write-Host "Контейнер: $ContainerName"
Write-Host ""

# Проверяем существование файла
if (-not (Test-Path $DataFile)) {
    Write-Host "❌ Файл $DataFile не найден!" -ForegroundColor Red
    exit 1
}

# Проверяем, запущен ли контейнер
$containerRunning = docker ps --filter "name=$ContainerName" --format "{{.Names}}" | Select-String -Pattern $ContainerName
if (-not $containerRunning) {
    Write-Host "❌ Контейнер $ContainerName не запущен!" -ForegroundColor Red
    Write-Host "Запустите контейнер командой: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "Загружаю данные в базу..." -ForegroundColor Yellow
try {
    Get-Content $DataFile | docker exec -i $ContainerName psql -U forum_owner -d forum_database
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Данные успешно загружены!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Проверка данных:" -ForegroundColor Cyan
        docker exec $ContainerName psql -U forum_owner -d forum_database -c "SELECT COUNT(*) as users FROM users; SELECT COUNT(*) as posts FROM posts; SELECT COUNT(*) as topics FROM topics;"
    } else {
        Write-Host ""
        Write-Host "❌ Ошибка при загрузке данных" -ForegroundColor Red
        Write-Host "Проверьте логи: docker logs $ContainerName" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "❌ Ошибка: $_" -ForegroundColor Red
    exit 1
}

