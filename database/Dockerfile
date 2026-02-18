FROM postgres:16-alpine

ENV POSTGRES_DB=forum_database \
    POSTGRES_USER=forum_owner \
    POSTGRES_PASSWORD=1111


COPY forum_database.sql /docker-entrypoint-initdb.d/01_forum_database.sql
COPY views.sql /docker-entrypoint-initdb.d/02_views.sql
COPY procedures.sql /docker-entrypoint-initdb.d/03_procedures.sql
COPY triggers.sql /docker-entrypoint-initdb.d/04_triggers.sql

COPY data_only.sql* /docker-entrypoint-initdb.d/05_data.sql

EXPOSE 5432