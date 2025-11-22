# Инструкция по развёртыванию серверной логики БД

## Шаг 1: Применение SQL объектов

### Применить все объекты (процедуры, триггеры, VIEW):
```bash
python manage.py apply_sql --type=all
```

### Применить только процедуры:
```bash
python manage.py apply_sql --type=procedures
```

### Применить только триггеры:
```bash
python manage.py apply_sql --type=triggers
```

### Применить только VIEW:
```bash
python manage.py apply_sql --type=views
```

## Шаг 2: Тестирование

### Запустить полный тест всех процедур и триггеров:
```bash
python manage.py test_procedures
```

## Шаг 3: Использование процедур

### Расчёт статистики пользователя:
```bash
python manage.py call_procedure calculate_user_statistics --user-id=1
```

### Пакетное обновление рейтингов тем:
```bash
python manage.py call_procedure batch_update_topic_ratings
```

### Архивация старых постов (старше 365 дней):
```bash
python manage.py call_procedure archive_old_posts --days=365
```

### Генерация аналитического отчёта:
```bash
python manage.py call_procedure generate_analytics_report --date-from=2024-01-01 --date-to=2024-12-31
```

### Массовая выдача достижений:
```bash
python manage.py call_procedure award_achievements_batch
```

### Обновление рангов пользователей:
```bash
python manage.py call_procedure update_user_ranks
```

## Шаг 4: Использование в коде

### Пример использования процедур в views:
```python
from GadukaGang.db_procedures import DatabaseProcedures, DatabaseViews

# Получить статистику пользователя
stats = DatabaseProcedures.calculate_user_statistics(user_id=1)

# Получить топ авторов
top_authors = DatabaseViews.get_top_contributors(limit=10)

# Генерация отчёта
report = DatabaseProcedures.generate_analytics_report(date_from, date_to)
```

## Созданные объекты БД

### Хранимые процедуры (7):
1. `calculate_user_statistics(user_id)` - статистика пользователя
2. `batch_update_topic_ratings()` - пакетное обновление рейтингов
3. `archive_old_posts(days_threshold)` - архивация старых постов
4. `generate_analytics_report(date_from, date_to)` - аналитический отчёт
5. `award_achievements_batch()` - массовая выдача достижений
6. `update_user_ranks()` - обновление рангов
7. `process_complaint_transaction()` - обработка жалоб с транзакцией

### Триггеры (8):
1. `trigger_audit_user_changes` - аудит изменений пользователей
2. `trigger_audit_post_changes` - аудит изменений постов
3. `trigger_update_last_activity_on_post` - обновление last_activity
4. `trigger_update_post_count` - обновление счётчика постов
5. `trigger_update_topic_last_post` - обновление даты последнего поста
6. `trigger_audit_moderator_actions` - аудит действий модераторов
7. `trigger_validate_subscription` - валидация подписок
8. `trigger_award_points_for_achievement` - начисление очков за достижения

### Представления VIEW (10):
1. `v_user_statistics` - статистика пользователей
2. `v_topic_statistics` - статистика тем
3. `v_active_users_24h` - активные пользователи (24ч)
4. `v_section_statistics` - статистика разделов
5. `v_top_contributors` - топ авторов
6. `v_daily_activity` - активность по дням
7. `v_popular_tags` - популярные теги
8. `v_moderation_statistics` - статистика модерации
9. `v_pending_complaints` - жалобы в ожидании
10. `v_system_activity` - системная активность

## Файлы

- `database/procedures.sql` - хранимые процедуры
- `database/triggers.sql` - триггеры
- `database/views.sql` - представления
- `GadukaGang/db_procedures.py` - утилиты для работы с БД
- `management/commands/apply_sql.py` - команда применения SQL
- `management/commands/call_procedure.py` - команда вызова процедур
- `management/commands/test_procedures.py` - команда тестирования
