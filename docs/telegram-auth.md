# Telegram Auth

Frontend передаёт неизменённый `Telegram.WebApp.initData` как
`Authorization: tma <initData>`. Backend строит data-check-string, вычисляет
HMAC-SHA256 с `WebAppData` и bot token, сравнивает подпись constant-time методом
и проверяет возраст `auth_date`.

Парсер ограничивает размер и число полей, запрещает дубли, требует `user` и
`auth_date`, отклоняет старые/будущие timestamps и возвращает 401 на повреждённые
данные. Dev-auth разрешён только вне production и требует `X-Dev-User`.

В production владелец задаётся через `OWNER_TELEGRAM_ID`; неизвестные Telegram ID
не получают роль владельца.

## Реальный E2E

Ручной GitHub workflow `Telegram E2E` проверяет настоящего бота через Bot API
`getMe`, доступность HTTPS Mini App, `/health` и подписанный запрос к
`/api/v1/fuels`.

Перед запуском задаются:

- secrets: `TELEGRAM_BOT_TOKEN`, `TEST_TELEGRAM_USER_ID`;
- variables: `API_URL`, `MINI_APP_URL`.

Token хранится только в GitHub Secrets и не выводится в логи или репозиторий.
