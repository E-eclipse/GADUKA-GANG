# Инструкция по настройке OAuth (GitHub и Google)

## 📋 Общая информация

Веб-форум "Gaduka Gang" поддерживает аутентификацию через OAuth провайдеры:
- **GitHub** - для разработчиков
- **Google** - универсальный провайдер

Используется библиотека `django-allauth` для реализации OAuth.

---

## 🔧 Настройка GitHub OAuth

### Шаг 1: Создание OAuth приложения на GitHub

1. Войдите в свой GitHub аккаунт
2. Перейдите в **Settings** → **Developer settings** → **OAuth Apps**
   - Или напрямую: https://github.com/settings/developers
3. Нажмите **"New OAuth App"** (или **"Register a new application"**)
4. Заполните форму:
   - **Application name**: `Gaduka Gang Forum` (или любое другое название)
   - **Homepage URL**: `http://localhost:9876` (для разработки) или ваш production URL
   - **Authorization callback URL**: `http://localhost:9876/accounts/github/login/callback/` (для разработки)
     - Для production: `https://yourdomain.com/accounts/github/login/callback/`
5. Нажмите **"Register application"**

### Шаг 2: Получение Client ID и Client Secret

После создания приложения вы увидите:
- **Client ID** - публичный идентификатор
- **Client Secret** - секретный ключ (нажмите "Generate a new client secret" если нужно)

⚠️ **Важно**: Client Secret нужно сохранить в безопасном месте!

### Шаг 3: Настройка в Django

#### Вариант 1: Через переменные окружения (рекомендуется)

1. Создайте файл `.env` в корне проекта `GadukaGang/`:
```env
GITHUB_CLIENT_ID=ваш_client_id
GITHUB_CLIENT_SECRET=ваш_client_secret
```

2. Обновите `settings.py`, раскомментируйте и настройте:
```python
SOCIALACCOUNT_PROVIDERS = {
    'github': {
        'APP': {
            'client_id': os.getenv('GITHUB_CLIENT_ID', ''),
            'secret': os.getenv('GITHUB_CLIENT_SECRET', ''),
            'key': ''
        }
    }
}
```

#### Вариант 2: Напрямую в settings.py (не рекомендуется для production)

```python
SOCIALACCOUNT_PROVIDERS = {
    'github': {
        'APP': {
            'client_id': 'ваш_client_id',
            'secret': 'ваш_client_secret',
            'key': ''
        }
    }
}
```

### Шаг 4: Применение миграций

```bash
cd GadukaGang
python manage.py migrate
```

### Шаг 5: Создание Social Application в админке Django

1. Запустите сервер: `python manage.py runserver`
2. Войдите в админку: http://localhost:9876/admin/
3. Перейдите в **Social accounts** → **Social applications**
4. Нажмите **"Add social application"**
5. Заполните:
   - **Provider**: `GitHub`
   - **Name**: `GitHub OAuth`
   - **Client id**: ваш Client ID
   - **Secret key**: ваш Client Secret
   - **Sites**: выберите ваш сайт (обычно `example.com`)
6. Нажмите **"Save"**

---

## 🔧 Настройка Google OAuth

### Шаг 1: Создание OAuth приложения в Google Cloud Console

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Перейдите в **APIs & Services** → **Credentials**
4. Нажмите **"Create Credentials"** → **"OAuth client ID"**
5. Если впервые, настройте OAuth consent screen:
   - **User Type**: External (для публичного использования)
   - **App name**: `Gaduka Gang Forum`
   - **User support email**: ваш email
   - **Developer contact information**: ваш email
   - Нажмите **"Save and Continue"**
   - В **Scopes** оставьте по умолчанию или добавьте `email`, `profile`
   - В **Test users** добавьте тестовые email (для тестового режима)
   - Нажмите **"Save and Continue"** → **"Back to Dashboard"**

6. Создайте OAuth Client ID:
   - **Application type**: `Web application`
   - **Name**: `Gaduka Gang Forum Web Client`
   - **Authorized JavaScript origins**: 
     - `http://localhost:9876` (для разработки)
     - `https://yourdomain.com` (для production)
   - **Authorized redirect URIs**:
     - `http://localhost:9876/accounts/google/login/callback/` (для разработки)
     - `https://yourdomain.com/accounts/google/login/callback/` (для production)
   - Нажмите **"Create"**

### Шаг 2: Получение Client ID и Client Secret

После создания вы увидите:
- **Client ID** - публичный идентификатор
- **Client Secret** - секретный ключ

⚠️ **Важно**: Сохраните Client Secret в безопасном месте!

### Шаг 3: Настройка в Django

#### Вариант 1: Через переменные окружения (рекомендуется)

1. Добавьте в файл `.env`:
```env
GOOGLE_CLIENT_ID=ваш_client_id
GOOGLE_CLIENT_SECRET=ваш_client_secret
```

2. Обновите `settings.py`:
```python
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID', ''),
            'secret': os.getenv('GOOGLE_CLIENT_SECRET', ''),
            'key': ''
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}
```

#### Вариант 2: Напрямую в settings.py

```python
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': 'ваш_client_id',
            'secret': 'ваш_client_secret',
            'key': ''
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}
```

### Шаг 4: Создание Social Application в админке Django

1. В админке Django перейдите в **Social accounts** → **Social applications**
2. Нажмите **"Add social application"**
3. Заполните:
   - **Provider**: `Google`
   - **Name**: `Google OAuth`
   - **Client id**: ваш Client ID
   - **Secret key**: ваш Client Secret
   - **Sites**: выберите ваш сайт
4. Нажмите **"Save"**

---

## 🚀 Использование OAuth

После настройки пользователи смогут:

1. Перейти на страницу входа: `/accounts/login/`
2. Увидеть кнопки "Sign in with GitHub" и "Sign in with Google"
3. Нажать на кнопку и авторизоваться через выбранный провайдер
4. После успешной авторизации будут автоматически зарегистрированы (если аккаунт новый) или войдут в систему

---

## 🔒 Безопасность

### Для разработки:
- Используйте `http://localhost:9876` в callback URLs
- Client Secret можно хранить в `.env` файле (не коммитьте в Git!)

### Для production:
- Используйте HTTPS (`https://yourdomain.com`)
- Храните секреты в переменных окружения сервера
- Добавьте `.env` в `.gitignore`
- Используйте сильные пароли для секретов

---

## 📝 Проверка работы

1. Запустите сервер: `python manage.py runserver`
2. Откройте: http://localhost:9876/accounts/login/
3. Должны появиться кнопки OAuth
4. Попробуйте войти через GitHub или Google

---

## ❗ Частые проблемы

### Проблема: "Redirect URI mismatch"
**Решение**: Убедитесь, что callback URL в настройках OAuth приложения точно совпадает с URL в Django (включая `/` в конце)

### Проблема: "Invalid client"
**Решение**: Проверьте, что Client ID и Client Secret правильно скопированы (без лишних пробелов)

### Проблема: OAuth кнопки не отображаются
**Решение**: 
- Проверьте, что `django-allauth` установлен: `pip install django-allauth`
- Проверьте, что в `INSTALLED_APPS` добавлены allauth приложения
- Выполните миграции: `python manage.py migrate`
- Проверьте, что Social Application создана в админке

### Проблема: Email верификация не работает
**Решение**: 
- Для разработки используйте `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` (письма выводятся в консоль)
- Для production настройте SMTP сервер

---

## 📚 Дополнительные ресурсы

- [django-allauth документация](https://docs.allauth.org/)
- [GitHub OAuth документация](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps)
- [Google OAuth документация](https://developers.google.com/identity/protocols/oauth2)

---

*Инструкция создана для веб-форума "Gaduka Gang"*

