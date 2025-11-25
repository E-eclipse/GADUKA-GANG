#!/bin/bash
# Скрипт для экспорта только данных из существующей БД
# Использование: ./export_data.sh [host] [port] [user] [database] [output_file]

HOST=${1:-localhost}
PORT=${2:-5432}
USER=${3:-forum_owner}
DATABASE=${4:-forum_database}
OUTPUT_FILE=${5:-data_only.sql}

echo "=========================================="
echo "Экспорт данных из базы данных"
echo "=========================================="
echo "Хост: $HOST:$PORT"
echo "База данных: $DATABASE"
echo "Пользователь: $USER"
echo "Выходной файл: $OUTPUT_FILE"
echo ""

# Экспортируем только данные (без схемы)
PGPASSWORD=1111 pg_dump \
    -h $HOST \
    -p $PORT \
    -U $USER \
    -d $DATABASE \
    --data-only \
    --no-owner \
    --no-acl \
    --inserts \
    -f $OUTPUT_FILE

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Данные успешно экспортированы в $OUTPUT_FILE"
    echo "Размер файла: $(du -h $OUTPUT_FILE | cut -f1)"
else
    echo ""
    echo "❌ Ошибка при экспорте данных"
    exit 1
fi

