# Быстрый старт: Переключение на реальную отправку email

## Что было исправлено:

✅ **Исправлено отображение пути в темах сообщества**
- Теперь для тем в сообществах показывается путь: "Сообщества / Название сообщества / Тема"
- Для обычных тем показывается: "Разделы / Название раздела / Тема"

## Как включить отправку email на реальную почту:

### Шаг 1: Создайте файл `.env`

В папке `GadukaGang/` (рядом с `manage.py`) создайте файл `.env` (с точкой в начале!)

### Шаг 2: Добавьте настройки

Скопируйте в файл `.env` одну из конфигураций:

**Для Gmail:**
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

### Шаг 3: Перезапустите сервер

1. Остановите сервер (Ctrl+C в терминале)
2. Запустите снова: `python manage.py runserver`

### Шаг 4: Проверьте работу

1. Создайте сообщество
2. Добавьте участников
3. Создайте тему в сообществе
4. Проверьте почту участников - они должны получить email

## ⚠️ Важно для Gmail:

Если используете Gmail, нужен **"Пароль приложения"**, а не обычный пароль:
1. Включите двухфакторную аутентификацию в Google аккаунте
2. Перейдите: https://myaccount.google.com/apppasswords
3. Создайте пароль приложения
4. Используйте этот пароль в `EMAIL_HOST_PASSWORD`

## Отладка:

Если письма не отправляются, проверьте:
- Файл называется `.env` (с точкой!)
- Нет лишних пробелов в настройках
- Правильность пароля
- Логи в консоли Django (там будут ошибки)

Подробная инструкция: `PRODUCTION_EMAIL_SETUP.md`

