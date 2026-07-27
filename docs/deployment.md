# Deployment

Docker Compose поднимает PostgreSQL, Redis, API и статический frontend. Для
production задайте секреты через менеджер секретов, HTTPS URL Mini App,
`APP_ENV=production`, `DEV_AUTH_ENABLED=false`, Telegram token, строгий CORS,
регулярные backup и миграции перед переключением версии.

