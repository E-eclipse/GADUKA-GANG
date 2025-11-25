#!/bin/bash
# Скрипт для загрузки данных в Docker контейнер
# Использование: ./load_data.sh [data_file.sql] [container_name]

DATA_FILE=${1:-data_only.sql}
CONTAINER_NAME=${2:-gadukagang-postgres}

if [ ! -f "$DATA_FILE" ]; then
    echo "❌ Файл $DATA_FILE не найден!"
    exit 1
fi

echo "=========================================="
echo "Загрузка данных в Docker контейнер"
echo "=========================================="
echo "Файл данных: $DATA_FILE"
echo "Контейнер: $CONTAINER_NAME"
echo ""

# Проверяем, запущен ли контейнер
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Контейнер $CONTAINER_NAME не запущен!"
    echo "Запустите контейнер командой: docker-compose up -d"
    exit 1
fi

echo "Загружаем данные в базу..."
cat "$DATA_FILE" | docker exec -i "$CONTAINER_NAME" psql -U forum_owner -d forum_database

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Данные успешно загружены!"
    echo ""
    echo "Проверка данных:"
    docker exec "$CONTAINER_NAME" psql -U forum_owner -d forum_database -c "SELECT COUNT(*) as users FROM users; SELECT COUNT(*) as posts FROM posts; SELECT COUNT(*) as topics FROM topics;"
else
    echo ""
    echo "❌ Ошибка при загрузке данных"
    echo "Проверьте логи: docker logs $CONTAINER_NAME"
    exit 1
fi

