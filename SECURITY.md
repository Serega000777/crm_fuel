# Security

Report vulnerabilities privately to the repository owner. Do not open public
issues containing tokens or personal data. Production requires a strong
`SECRET_KEY`, HTTPS, disabled dev-auth, trusted CORS origins, PostgreSQL backups
and a real Telegram bot token.

Production startup fails closed unless dev-auth is disabled, a bot token and
owner Telegram ID are configured, CORS origins are explicit, and the application
secret is non-default. See [the latest audit](docs/security-audit.md).
