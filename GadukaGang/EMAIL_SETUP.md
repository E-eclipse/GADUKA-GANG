# Настройка Email-уведомлений

## Настройка SMTP для отправки email

Для работы email-уведомлений необходимо настроить SMTP сервер. Добавьте следующие переменные в ваш `.env` файл:

### Для Gmail:
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=почта
EMAIL_HOST_PASSWORD=пароль
DEFAULT_FROM_EMAIL=дефолт почта
SITE_URL=http://127.0.0.1:8000
```

**Важно для Gmail:**
- Нужно использовать "Пароль приложения" (App Password), а не обычный пароль
- Включите двухфакторную аутентификацию в Google аккаунте
- Создайте пароль приложения: https://myaccount.google.com/apppasswords

### Для Yandex:
```env
EMAIL_HOST=smtp.yandex.ru
EMAIL_PORT=465
EMAIL_USE_SSL=true
EMAIL_HOST_USER=почта
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=дефолт почта
SITE_URL=http://127.0.0.1:8000
```

### Для Mail.ru:
```env
EMAIL_HOST=smtp.mail.ru
EMAIL_PORT=465
EMAIL_USE_SSL=true
EMAIL_HOST_USER=почта
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=дефолт почта
SITE_URL=http://127.0.0.1:8000
```

### Для других SMTP серверов:
```env
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
EMAIL_HOST_USER=your-email@your-provider.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=noreply@gadukagang.com
SITE_URL=http://127.0.0.1:8000
```

## Как это работает

1. **Уведомления о новых темах в сообществах:**
   - Когда кто-то создает тему в сообществе, все участники получают email-уведомление
   - Автор темы не получает уведомление
   - Пользователи могут отключить уведомления через настройки сообщества

2. **Уведомления о новых сообщениях:**
   - Когда кто-то добавляет сообщение в тему сообщества, все участники получают email-уведомление
   - Автор сообщения не получает уведомление
   - Пользователи могут отключить уведомления через настройки сообщества

## Тестирование

Для тестирования в режиме разработки (без реальной отправки):
- Не указывайте `EMAIL_HOST` в `.env` - система будет использовать console backend
- Все письма будут выводиться в консоль Django

## Проверка работы

1. Создайте сообщество
2. Добавьте участников
3. Создайте тему в сообществе
4. Проверьте, что участники получили email-уведомления

