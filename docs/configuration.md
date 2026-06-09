# Конфигурация

При первом запуске создаётся `.env` с дефолтными значениями.

## Обязательные

```env
BOT_TOKEN=<токен от @BotFather>
ENABLED_IDS=<telegram_id через пробел>
DOMAIN=<домен для входящих писем>
```

## Опциональные

```env
SMTP_HOST=0.0.0.0
SMTP_PORT=25
SESSION_MINUTES=5
LOG_FILE=LeetBot.log
ENCRYPT_KEY=              # hex 32 байта; генерируется автоматически
ADMIN_IDS=                # telegram_id администраторов через пробел
API_HOST=0.0.0.0
API_PORT=7625
TOKEN_TTL_DAYS=30
SSL_CERTFILE=             # путь к cert.pem (TLS для API)
SSL_KEYFILE=              # путь к privkey.pem
```

`ENCRYPT_KEY` генерируется один раз и сохраняется в `.env`. Смена ключа делает все ранее выданные адреса недействительными.
