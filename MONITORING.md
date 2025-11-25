## Мониторинг и метрики GadukaGang

Этот проект теперь публикует метрики Prometheus через `django_prometheus` и предоставляет готовую инфраструктуру для Prometheus + Grafana.

### 1. Django + Prometheus

- Библиотека `django-prometheus` добавлена в `INSTALLED_APPS`, middleware и в качестве бэкенда БД.
- Эндпоинт `/metrics` автоматически отдаёт все стандартные и кастомные метрики.
- Кастомные метрики:
  - `gaduka_active_users_total` — количество активных пользователей (фильтр `is_active=True`).
  - `gaduka_communities_total` — количество сообществ.
  - `gaduka_posts_total` — количество опубликованных постов (без помеченных как удалённые).

Метрики не аннулируются при перезапуске: значения берутся из БД каждый раз, когда изменяются связанные модели.

### 2. Docker-инфраструктура

Запустите весь стек командой:

```powershell
docker compose up --build
```

- Django (`frontend`) доступен на `http://localhost:9876`.
- Prometheus — `http://localhost:9090`.
- Grafana — `http://localhost:3000` (логин/пароль по умолчанию `admin` / `admin`, можно переопределить переменными `GRAFANA_ADMIN_USER`/`GRAFANA_ADMIN_PASSWORD`).

Prometheus конфигурация лежит в `monitoring/prometheus/prometheus.yml` и с 15‑секундным интервалом опрашивает `frontend:8000/metrics`.

### 3. Grafana

- Datasource автоматически подхватывается из `monitoring/grafana/provisioning/datasources/datasource.yml`.
- Дашборд `GadukaGang Monitoring` загружается из `monitoring/grafana/dashboards/gadukagang-overview.json` и содержит три панели:
  1. **Активные пользователи** (`gaduka_active_users_total`) — быстрый стат-показатель.
  2. **Сообщества** (`gaduka_communities_total`) — временной график с легендой (`last` и `max`).
  3. **Активность постов** — одновременно выводит `gaduka_posts_total` и скорость появления постов `rate(gaduka_posts_total[5m])`.

Каждая панель уже оформлена с подходящими подписями и легендой. Можно добавлять новые метрики прямо из Prometheus, все они автоматически попадают в `/metrics`.

### 4. Быстрая проверка

1. Соберите контейнеры: `docker compose up --build`.
2. Перейдите на `http://localhost:9876/metrics` — вы увидите все экспортируемые значения.
3. Откройте Grafana `http://localhost:3000`, авторизуйтесь и выберите дашборд **GadukaGang Monitoring**.
4. Создайте пару постов/сообществ — графики обновятся за 15–30 секунд.

### 5. Полезные запросы

- `rate(http_requests_total{handler="api"}[5m])` — нагрузка на API.
- `gaduka_active_users_total` — количество активных пользователей.
- `increase(gaduka_posts_total[1h])` — прирост постов за час.

При необходимости можно расширять `GadukaGang/GadukaGang/prometheus_metrics.py`, добавляя новые `Gauge`/`Counter` и подписываясь на сигналы Django.

### 6. Алертинг (Alerting)

Grafana настроена для отправки уведомлений через Telegram и Email/Webhook. Подробная инструкция по настройке находится в файле **`GRAFANA_ALERTING_GUIDE.md`**.

**Быстрый старт:**
1. Создайте Telegram бота через [@BotFather](https://t.me/BotFather)
2. В Grafana: **Alerting → Contact points → New contact point**
3. Выберите **Telegram**, укажите токен бота и Chat ID
4. Создайте **Alert rule** для любой метрики (например, `rate(django_http_requests_total{status="404"}[5m]) > 0.1`)
5. Настройте уведомления на ваш Contact Point

**Состояния алертов:**
- **Normal** — всё в порядке
- **Pending** — условие выполнено, но ещё не прошло время ожидания
- **Firing** — алерт сработал, отправлено уведомление
- **Resolved** — проблема решена, отправлено уведомление о восстановлении

### 7. Дашборды

Доступны два дашборда:
- **GadukaGang Monitoring** (`gadukagang-overview`) — общий мониторинг приложения
- **404 Errors Dashboard** (`404-errors`) — детальная визуализация 404 ошибок по времени, методам HTTP и периодам

Дашборд 404 ошибок включает:
- Скорость 404 ошибок (запросов/сек)
- График по времени
- Всего 404 за час
- Распределение по HTTP методам (GET, POST и т.д.)
- Накопленные значения за 5 минут, 1 час и 24 часа

