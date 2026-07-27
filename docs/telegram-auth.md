# Telegram Auth

Frontend передаёт неизменённый `Telegram.WebApp.initData` как `Authorization:
tma <initData>`. Backend строит data-check-string, вычисляет HMAC-SHA256 с
секретом `WebAppData` и токеном бота, сравнивает подпись constant-time методом
и проверяет возраст `auth_date`.

Парсер ограничивает размер и число полей, запрещает дубли, проверяет обязательные
`user`/`auth_date`, отклоняет будущие timestamps и возвращает 401 вместо
внутренней ошибки на повреждённых данных.

Dev-auth разрешён только вне production и требует `X-Dev-User`. Telegram user ID
после проверки используется для RBAC; данные пользователя из frontend без
подписи не считаются доверенными.

В production первый владелец задаётся только через `OWNER_TELEGRAM_ID`;
неизвестные Telegram ID автоматически не получают доступ.
