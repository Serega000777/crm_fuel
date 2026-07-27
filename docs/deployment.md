# Deployment

Docker Compose поднимает PostgreSQL, Redis, API и статический frontend. Для
production задайте секреты через менеджер секретов, HTTPS URL Mini App,
`APP_ENV=production`, `DEV_AUTH_ENABLED=false`, Telegram token, строгий CORS,
регулярные backup и миграции перед переключением версии.

Обязательные production-переменные: `OWNER_TELEGRAM_ID`,
`TELEGRAM_BOT_TOKEN`, безопасный `SECRET_KEY`, явный `CORS_ORIGINS`,
`APP_ENV=production` и `DEV_AUTH_ENABLED=false`. Backend и frontend запускаются
не от root, с read-only filesystem. Перед релизом выполните PostgreSQL
upgrade/downgrade rehearsal и проверку восстановления backup.
