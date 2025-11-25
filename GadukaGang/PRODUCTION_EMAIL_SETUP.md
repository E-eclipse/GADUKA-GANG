# Переключение в продакшн режим для Email

## Как переключиться из режима разработки в продакшн

### Текущий режим (разработка)
Сейчас система использует `console.EmailBackend` - все письма выводятся в консоль Django, реальная отправка не происходит.

### Продакшн режим
Для реальной отправки email на почту нужно добавить настройки SMTP в файл `.env`.

## Шаги для переключения:

### 1. Создайте или откройте файл `.env`

Файл должен находиться в корне проекта `GadukaGang/` (рядом с `manage.py`).

### 2. Добавьте настройки SMTP

Добавьте следующие строки в файл `.env`:

**Для Gmail (рекомендуется):**
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=simernin.mat@gmail.com
EMAIL_HOST_PASSWORD=Bprc28gk
DEFAULT_FROM_EMAIL=noreply@gadukagang.com
SITE_URL=http://127.0.0.1:8000
```

**Для Yandex:**
```env
EMAIL_HOST=smtp.yandex.ru
EMAIL_PORT=465
EMAIL_USE_SSL=true
EMAIL_HOST_USER=matveisimernin@yandex.ru
EMAIL_HOST_PASSWORD=Bprc28gk
DEFAULT_FROM_EMAIL=noreply@gadukagang.com
SITE_URL=http://127.0.0.1:8000
```

### 3. Перезапустите сервер Django

После добавления настроек в `.env`:
1. Остановите сервер (Ctrl+C)
2. Запустите снова: `python manage.py runserver`

### 4. Проверка работы

Система автоматически определит, что `EMAIL_HOST` указан, и переключится на SMTP backend.

**Как проверить:**
1. Создайте сообщество
2. Добавьте участников
3. Создайте тему в сообществе
4. Проверьте почту участников - они должны получить email-уведомление

## Важные замечания

### Для Gmail:
- ⚠️ **Важно:** Используйте "Пароль приложения" (App Password), а не обычный пароль
- Включите двухфакторную аутентификацию в Google аккаунте
- Создайте пароль приложения: https://myaccount.google.com/apppasswords
- Обычный пароль не будет работать!

### Для Yandex:
- Можно использовать обычный пароль
- Убедитесь, что включена возможность отправки через SMTP в настройках почты

## Отладка

Если письма не отправляются:

1. **Проверьте настройки в `.env`:**
   - Убедитесь, что файл называется именно `.env` (с точкой в начале)
   - Проверьте, что нет лишних пробелов
   - Проверьте правильность пароля

2. **Проверьте логи Django:**
   - В консоли будут выводиться ошибки отправки
   - Ищите сообщения типа "SMTPAuthenticationError" или "Connection refused"

3. **Тестовый запуск:**
   ```bash
   python manage.py shell
   ```
   Затем в shell:
   ```python
   from django.core.mail import send_mail
   send_mail('Test', 'Test message', 'noreply@gadukagang.com', ['your-email@example.com'])
   ```

## Возврат в режим разработки

Если нужно вернуться к режиму разработки (вывод в консоль):
- Удалите или закомментируйте строку `EMAIL_HOST=...` в `.env`
- Перезапустите сервер

