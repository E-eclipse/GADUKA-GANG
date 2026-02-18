FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Установка зависимостей
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости и убираем кэш
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем директорию app
COPY . /app/

# Создание необходимых дирректорий
RUN mkdir -p /app/staticfiles /app/media /app/backups /app/temp_exports

# Разраничение прав (чтение и выполнение для всех)
RUN chmod -R 755 /app

EXPOSE 8000

# Перезапись сервера в докер компоуз
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]