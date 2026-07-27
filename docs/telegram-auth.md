# Telegram Auth

Frontend передаёт неизменённый `Telegram.WebApp.initData` как `Authorization:
tma <initData>`. Backend строит data-check-string, вычисляет HMAC-SHA256 с
секретом `WebAppData` и токеном бота, сравнивает подпись constant-time методом
и проверяет возраст `auth_date`.

Dev-auth разрешён только вне production и требует `X-Dev-User`. Telegram user ID
после проверки используется для RBAC; данные пользователя из frontend без
подписи не считаются доверенными.

