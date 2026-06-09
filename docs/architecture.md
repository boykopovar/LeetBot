# Архитектура

```
main.py
├── aiogram Bot + Dispatcher          # Telegram long-polling
│   ├── UpdateLogMiddleware           # логирование каждого апдейта
│   ├── EnabledUserFilter             # белый список ENABLED_IDS
│   ├── /random  -- RandomCmdRouter   # генерация нового адреса
│   ├── /apikey  -- ApikeyCmdRouter   # выдача JWT для REST API
│   └── <text>   -- EmailCmdRouter    # ввод существующего адреса
│
├── aiosmtpd SMTP-сервер
│   ├── handle_RCPT                   # проверка адреса по реестру сессий
│   └── handle_DATA                   # парсинг MIME, send_document
│
└── FastAPI REST API (uvicorn)
    └── /mail  -- mail router         # управление сессиями через HTTP
```

| Путь | Ответственность |
|---|---|
| `src/domain/` | Доменные модели (`ApiToken`, `MailMessage`) |
| `src/ports/` | Протоколы (`TokenSigner`, `SessionStore`, `Mailbox`) |
| `src/infrastructure/` | `InMemorySessionStore`, `InMemoryMailbox` |
| `src/services/token_service.py` | JWT HS256 |
| `src/services/random_email_service.py` | Feistel-биекция для генерации и верификации адресов |
| `src/services/mail_parser.py` | Парсинг MIME, извлечение HTML/plain, X-Originating-IP |
| `src/services/caption_service.py` | Форматирование подписи к письму |
| `src/services/filename_service.py` | Имя файла из Subject или From |
| `src/smtp/handler.py` | SMTP-обработчик (RCPT + DATA) |
| `src/smtp/server.py` | Фабрика asyncio-сервера |
| `src/smtp/log_filter.py` | Подавление шума aiosmtpd |
| `src/telegram/middleware.py` | Логирование апдейтов + EMA времени обработки |
| `src/env_tools.py` | Загрузка `.env`, генерация `ENCRYPT_KEY` |
| `src/logger.py` | INFO на stdout, WARNING+ в файл |
