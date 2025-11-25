# Быстрая настройка SMTP для Grafana

## Проблема
Ошибка: `Failed to send test alert.: SMTP not configured`

## Решение 1: Настройка через переменные окружения (рекомендуется)

### Шаг 1: Откройте `docker-compose.yaml`
Найдите секцию `grafana` → `environment`

### Шаг 2: Добавьте/измените переменные для Gmail

```yaml
environment:
  - GF_SMTP_ENABLED=true
  - GF_SMTP_HOST=smtp.gmail.com
  - GF_SMTP_PORT=587
  - GF_SMTP_USER=ваш_email@gmail.com
  - GF_SMTP_PASSWORD=ваш_пароль_приложения  # ⚠️ НЕ обычный пароль!
  - GF_SMTP_FROM_ADDRESS=ваш_email@gmail.com
  - GF_SMTP_SKIP_VERIFY=false
```

### Шаг 3: Получите "Пароль приложения" для Gmail

1. Перейдите: https://myaccount.google.com/security
2. Включите **2-Step Verification** (если не включена)
3. Перейдите: https://myaccount.google.com/apppasswords
4. Выберите:
   - **App**: Mail
   - **Device**: Other (Custom name) → введите "Grafana"
5. Нажмите **Generate**
6. **Скопируйте 16-значный пароль** (без пробелов)
7. Вставьте в `GF_SMTP_PASSWORD`

### Шаг 4: Перезапустите Grafana

```powershell
docker compose restart grafana
```

### Шаг 5: Проверьте в Grafana UI

1. Откройте: http://localhost:3000
2. Перейдите: **Administration → Settings → SMTP**
3. Должны быть видны настройки из переменных окружения
4. Нажмите **"Send test email"** → должно прийти письмо

---

## Решение 2: Использовать .env файл (безопаснее)

### Шаг 1: Создайте `.env` в корне проекта

```env
# Grafana SMTP настройки
GRAFANA_SMTP_ENABLED=true
GRAFANA_SMTP_HOST=smtp.gmail.com
GRAFANA_SMTP_PORT=587
GRAFANA_SMTP_USER=ваш_email@gmail.com
GRAFANA_SMTP_PASSWORD=ваш_пароль_приложения
GRAFANA_SMTP_FROM_ADDRESS=ваш_email@gmail.com
GRAFANA_SMTP_SKIP_VERIFY=false
```

### Шаг 2: Перезапустите

```powershell
docker compose restart grafana
```

**Важно**: Добавьте `.env` в `.gitignore`, чтобы не коммитить пароли!

---

## Решение 3: Использовать Webhook вместо Email (самый простой способ)

Если не хотите настраивать SMTP, используйте Webhook:

### Шаг 1: Откройте https://webhook.site

### Шаг 2: Скопируйте уникальный URL
Например: `https://webhook.site/12345678-1234-1234-1234-123456789abc`

### Шаг 3: В Grafana создайте Contact Point
1. **Alerting → Contact points → New contact point**
2. **Name**: `Webhook Notifications`
3. **Integration**: **Webhook**
4. **URL**: вставьте URL из webhook.site
5. **Save**

### Шаг 4: Тест
1. Нажмите **"Test"** в Contact Point
2. На webhook.site увидите JSON с данными алерта

**Преимущества Webhook:**
- ✅ Не требует настройки SMTP
- ✅ Работает сразу
- ✅ Видно все данные в реальном времени
- ✅ Подходит для демонстрации

---

## Альтернативные SMTP серверы

### Yandex Mail
```yaml
- GF_SMTP_HOST=smtp.yandex.ru
- GF_SMTP_PORT=465
- GF_SMTP_USER=ваш_email@yandex.ru
- GF_SMTP_PASSWORD=ваш_пароль
- GF_SMTP_FROM_ADDRESS=ваш_email@yandex.ru
```
**Примечание**: Для Yandex может потребоваться `GF_SMTP_SKIP_VERIFY=true`

### Mail.ru
```yaml
- GF_SMTP_HOST=smtp.mail.ru
- GF_SMTP_PORT=465
- GF_SMTP_USER=ваш_email@mail.ru
- GF_SMTP_PASSWORD=ваш_пароль
- GF_SMTP_FROM_ADDRESS=ваш_email@mail.ru
```

### Outlook/Hotmail
```yaml
- GF_SMTP_HOST=smtp-mail.outlook.com
- GF_SMTP_PORT=587
- GF_SMTP_USER=ваш_email@outlook.com
- GF_SMTP_PASSWORD=ваш_пароль
- GF_SMTP_FROM_ADDRESS=ваш_email@outlook.com
```

---

## Troubleshooting

### Ошибка: "SMTP not configured"
- Проверьте, что `GF_SMTP_ENABLED=true`
- Убедитесь, что все переменные заполнены
- Перезапустите Grafana: `docker compose restart grafana`

### Ошибка: "Authentication failed"
- Для Gmail используйте **"Пароль приложения"**, не обычный пароль
- Убедитесь, что 2-Step Verification включена

### Ошибка: "Connection timeout"
- Проверьте порт (587 для TLS, 465 для SSL)
- Проверьте, не блокирует ли firewall порт
- Попробуйте `GF_SMTP_SKIP_VERIFY=true` (небезопасно, но для теста)

### Проверка логов
```powershell
docker logs gadukagang-grafana | grep -i smtp
```

### Проверка настроек в UI
1. Administration → Settings → SMTP
2. Должны быть видны все настройки
3. Нажмите "Send test email"

---

## Рекомендация для демонстрации

Для быстрой демонстрации работы алертов **используйте Webhook** (Решение 3):
- Настройка занимает 2 минуты
- Не требует паролей и SMTP
- Все уведомления видны на webhook.site
- Подходит для показа Firing и Resolved состояний

Email можно настроить позже, если нужно.

