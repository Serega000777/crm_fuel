# Развёртывание

Docker Compose запускает PostgreSQL, Redis, API, frontend и ежедневное резервное
копирование базы. Для production задайте переменные через секреты хостинга или
закрытый `.env`, который не добавляется в Git.

## Обязательные настройки production

- `APP_ENV=production`
- `DEV_AUTH_ENABLED=false`
- `TELEGRAM_BOT_TOKEN`
- `OWNER_TELEGRAM_ID`
- `SECRET_KEY` — случайная строка не короче 32 символов
- `CORS_ORIGINS` — точный HTTPS-адрес Mini App
- `RATE_LIMIT_ENABLED=true`
- `REDIS_URL`
- отдельные безопасные `POSTGRES_USER` и `POSTGRES_PASSWORD`

Backend завершает запуск с ошибкой, если production-конфигурация небезопасна или
Redis недоступен. Лимиты по умолчанию: 120 чтений и 30 изменений в минуту на
пользователя/IP. Они задаются через `RATE_LIMIT_READ_PER_MINUTE` и
`RATE_LIMIT_WRITE_PER_MINUTE`.

## Миграции и запуск

Перед переключением версии создайте backup. Backend выполняет
`alembic upgrade head` перед запуском API. Контейнеры работают не от root, с
read-only filesystem и `no-new-privileges`.

## Резервные копии

Сервис `backup` создаёт PostgreSQL custom-format dump в volume
`postgres_backups`, проверяет его через `pg_restore --list` и удаляет файлы старше
`BACKUP_RETENTION_DAYS` (по умолчанию 14 дней). Интервал задаётся
`BACKUP_INTERVAL_SECONDS` (по умолчанию 86400).

Разовый backup:

```bash
docker compose run --rm backup /bin/sh /opt/backup/backup.sh
```

Просмотр файлов:

```bash
docker compose run --rm backup ls -lh /backups
```

Восстановление перезаписывает текущую базу. Сначала остановите backend и передайте
точное имя проверенного файла:

```bash
docker compose stop backend
docker compose run --rm backup /bin/sh /opt/backup/restore.sh \
  /backups/crm_fuel_YYYYMMDDTHHMMSSZ.dump
docker compose start backend
```

Проверку восстановления нужно регулярно выполнять на отдельной тестовой базе.
Наличие backup без успешной проверки restore не считается гарантией восстановления.

CI выполняет автоматический restore rehearsal: создаёт контрольную запись, делает
custom-format dump, восстанавливает его в отдельную базу и сверяет marker. После
развёртывания тот же rehearsal необходимо повторить на инфраструктуре хостинга.
