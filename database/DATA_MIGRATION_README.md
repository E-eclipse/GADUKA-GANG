# Инструкция по переносу данных в Docker

Эта инструкция поможет вам перенести данные из существующей базы данных в Docker контейнер.

## Способ 1: Автоматическая загрузка при инициализации (рекомендуется)

Этот способ загрузит данные автоматически при первом запуске контейнера.

### Шаг 1: Экспорт данных из существующей БД

**Windows PowerShell:**
```powershell
cd database
.\export_data.ps1 -Host localhost -Port 5432 -User forum_owner -Database forum_database -OutputFile data_only.sql
# Или с параметрами по умолчанию:
.\export_data.ps1
```

**Windows CMD:**
```cmd
cd database
.\export_data.bat [host] [port] [user] [database] [output_file]
```

**Linux/Mac:**
```bash
cd database
chmod +x export_data.sh
./export_data.sh [host] [port] [user] [database] [output_file]
```

**Примеры:**
```cmd
REM Экспорт из локальной БД
export_data.bat localhost 5432 forum_owner forum_database data_only.sql

REM Экспорт из другой БД
export_data.bat 192.168.1.100 5432 myuser mydatabase data_only.sql
```

Если параметры не указаны, используются значения по умолчанию:
- host: `localhost`
- port: `5432`
- user: `forum_owner`
- database: `forum_database`
- output_file: `data_only.sql`

### Шаг 2: Размещение файла данных

Скопируйте созданный файл `data_only.sql` в папку `database/`:
```
database/
  ├── Dockerfile
  ├── forum_database.sql
  ├── views.sql
  ├── procedures.sql
  ├── triggers.sql
  └── data_only.sql  ← Поместите файл сюда
```

### Шаг 3: Пересборка и запуск контейнера

```bash
# Остановите и удалите существующий контейнер (если запущен)
docker-compose down -v

# Пересоберите образ с данными
docker-compose build postgres

# Запустите контейнеры
docker-compose up -d
```

Данные будут автоматически загружены при инициализации базы данных.

---

## Способ 2: Загрузка данных в уже запущенный контейнер

Если контейнер уже запущен и вы хотите загрузить данные без пересборки:

### Шаг 1: Экспорт данных

Выполните шаг 1 из Способа 1.

### Шаг 2: Загрузка данных в контейнер

**Windows PowerShell:**
```powershell
cd database
.\load_data.ps1 -DataFile data_only.sql -ContainerName gadukagang-postgres
# Или с параметрами по умолчанию:
.\load_data.ps1
```

**Windows CMD:**
```cmd
cd database
.\load_data.bat data_only.sql gadukagang-postgres
```

**Linux/Mac:**
```bash
cd database
chmod +x load_data.sh
./load_data.sh data_only.sql gadukagang-postgres
```

**Пример:**
```cmd
REM Загрузка данных
load_data.bat data_only.sql gadukagang-postgres

REM Или с указанием другого файла
load_data.bat backups/backup_20251122_191754.sql gadukagang-postgres
```

---

## Способ 3: Ручная загрузка через psql

Если скрипты не работают, можно загрузить данные вручную:

### Шаг 1: Скопируйте файл в контейнер
```bash
docker cp data_only.sql gadukagang-postgres:/tmp/data.sql
```

### Шаг 2: Загрузите данные
```bash
docker exec -i gadukagang-postgres psql -U forum_owner -d forum_database < data_only.sql
```

Или через интерактивный режим:
```bash
docker exec -it gadukagang-postgres psql -U forum_owner -d forum_database
```

Затем в psql:
```sql
\i /tmp/data.sql
```

---

## Способ 4: Использование существующего бэкапа

Если у вас уже есть полный бэкап БД (например, `backup_20251122_191754.sql`):

### Вариант А: Извлечь только данные из бэкапа

1. Откройте файл бэкапа в текстовом редакторе
2. Найдите секцию с `COPY` или `INSERT` командами (данные)
3. Скопируйте только эти команды в новый файл `data_only.sql`
4. Убедитесь, что в начале файла есть:
   ```sql
   -- Отключаем проверки внешних ключей для быстрой загрузки
   SET session_replication_role = 'replica';
   ```
5. В конце файла добавьте:
   ```sql
   -- Включаем обратно
   SET session_replication_role = 'origin';
   ```

### Вариант Б: Использовать полный бэкап (перезапишет схему)

⚠️ **Внимание:** Это перезапишет всю схему БД!

```bash
# Остановите контейнер
docker-compose down -v

# Скопируйте бэкап в папку database
cp GadukaGang/backups/backup_20251122_191754.sql database/restore.sql

# Измените Dockerfile временно, заменив forum_database.sql на restore.sql
# Или используйте load_data.bat после запуска контейнера
```

---

## Проверка загрузки данных

После загрузки данных проверьте, что они загрузились:

```bash
# Подключитесь к БД
docker exec -it gadukagang-postgres psql -U forum_owner -d forum_database

# Проверьте количество записей
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM posts;
SELECT COUNT(*) FROM topics;
SELECT COUNT(*) FROM sections;
```

---

## Решение проблем

### Ошибка: "relation does not exist"
- Убедитесь, что схема БД создана перед загрузкой данных
- Проверьте порядок выполнения скриптов в `/docker-entrypoint-initdb.d/`

### Ошибка: "duplicate key value"
- Данные уже загружены. Остановите контейнер и удалите volume:
  ```bash
  docker-compose down -v
  docker-compose up -d
  ```

### Ошибка: "permission denied"
- Убедитесь, что файлы скриптов имеют права на выполнение:
  ```bash
  chmod +x export_data.sh load_data.sh
  ```

### Данные не загружаются
- Проверьте логи контейнера:
  ```bash
  docker logs gadukagang-postgres
  ```
- Убедитесь, что файл `data_only.sql` содержит только команды INSERT/COPY, без CREATE TABLE

---

## Примечания

- Файл `data_only.sql` должен содержать только данные (INSERT/COPY), не схему
- При использовании Способа 1, файл `data_only.sql` должен быть в папке `database/` до сборки образа
- Если вы изменили схему БД, убедитесь, что данные совместимы с новой схемой
- Рекомендуется делать бэкап перед загрузкой данных

