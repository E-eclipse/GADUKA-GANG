# 🚀 Быстрый старт: Загрузка данных в Docker

## Самый простой способ (если у вас есть бэкап)

Если у вас уже есть файл бэкапа (например, `GadukaGang/backups/backup_20251122_191754.sql`):

**PowerShell:**
```powershell
cd database
.\quick_load.ps1 ..\GadukaGang\backups\backup_20251122_191754.sql
```

**CMD:**
```cmd
cd database
quick_load.bat ..\GadukaGang\backups\backup_20251122_191754.sql
```

Готово! Данные загружены.

---

## Если нужно экспортировать данные из существующей БД

### Шаг 1: Экспорт данных

**PowerShell:**
```powershell
cd database
.\export_data.ps1
```

**CMD:**
```cmd
cd database
.\export_data.bat
```

Это создаст файл `data_only.sql` с данными из вашей БД.

### Шаг 2: Загрузка в Docker

**Вариант А:** Автоматическая загрузка при запуске
1. Скопируйте `data_only.sql` в папку `database/`
2. Пересоберите контейнер: `docker-compose build postgres`
3. Запустите: `docker-compose up -d`

**Вариант Б:** Загрузка в уже запущенный контейнер

**PowerShell:**
```powershell
.\load_data.ps1 data_only.sql
```

**CMD:**
```cmd
.\load_data.bat data_only.sql
```

---

## Проверка

После загрузки проверьте данные:

```cmd
docker exec -it gadukagang-postgres psql -U forum_owner -d forum_database -c "SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM posts;"
```

---

📖 Подробная инструкция: [DATA_MIGRATION_README.md](DATA_MIGRATION_README.md)

