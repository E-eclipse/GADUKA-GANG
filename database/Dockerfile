FROM postgres:16-alpine

ENV POSTGRES_DB=forum_database \
    POSTGRES_USER=forum_owner \
    POSTGRES_PASSWORD=1111

COPY forum_database.sql /docker-entrypoint-initdb.d/01_forum_database.sql

EXPOSE 5432