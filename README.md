# LeetBot

Telegram-бот: принимает входящие письма на временный email-адрес, пересылает пользователю в Telegram как HTML-документ. Встроенный SMTP-сервер, без сторонних почтовых сервисов.

---

## Архитектура

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
| `src/domain/` | Доменные модели (`ApiToken`, `EmailSession`) |
| `src/ports/` | Протоколы (`TokenSigner`, `SessionStore`) |
| `src/infrastructure/` | `InMemorySessionStore` |
| `src/services/token_service.py` | JWT HS256 без зависимостей |
| `src/services/random_email_service.py` | Feistel-биекция для генерации/верификации адресов |
| `src/services/mail_parser.py` | Парсинг MIME, извлечение HTML/plain |
| `src/services/caption_service.py` | Форматирование подписи к письму |
| `src/services/filename_service.py` | Имя файла из Subject или From |
| `src/smtp/handler.py` | SMTP-обработчик (RCPT + DATA) |
| `src/smtp/server.py` | Фабрика asyncio-сервера |
| `src/smtp/log_filter.py` | Подавление шума aiosmtpd |
| `src/telegram/middleware.py` | Логирование апдейтов + EMA времени обработки |
| `src/env_tools.py` | Загрузка `.env`, генерация `ENCRYPT_KEY` |
| `src/logger.py` | INFO на stdout, WARNING+ в файл |

---

## Установка

```
Python 3.8+
```

```bash
pip install aiogram aiosmtpd email-validator python-dotenv fastapi uvicorn
```

---

## Конфигурация

При первом запуске создаётся `.env` с дефолтными значениями.

**Обязательные:**

```env
BOT_TOKEN=<токен от @BotFather>
ENABLED_IDS=<telegram_id через пробел>
DOMAIN=<домен для входящих писем>
```

**Опциональные:**

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

> `ENCRYPT_KEY` генерируется один раз и сохраняется в `.env`. Смена ключа делает все ранее выданные адреса недействительными.

---

## Запуск

```bash
python main.py
```

SMTP-сервер, Telegram polling и REST API стартуют одновременно в одном asyncio event loop.

---

## Telegram-команды

| Команда / ввод | Действие |
|---|---|
| `/random` | Генерирует новый адрес, активирует сессию |
| `/apikey` | Возвращает JWT-ключ для REST API и ссылку на документацию |
| `localpart` | Активирует сессию на `localpart@DOMAIN` (адрес должен принадлежать пользователю) |
| `local@domain` | То же, с явным доменом |

---

## REST API

Интерактивная документация: `https://<API_HOST>:<API_PORT>/docs`

Аутентификация — Bearer JWT, получить через `/apikey` в Telegram.

```
Authorization: Bearer <token>
```

### Эндпоинты

#### `GET /mail/session`

Возвращает активную сессию текущего пользователя.

**Ответы:**

| Код | Тело | Условие |
|---|---|---|
| 200 | `{"email": "...", "expires_in_minutes": N}` | Сессия активна |
| 404 | `{"detail": "No active session"}` | Нет активной сессии |
| 401 | `{"detail": "Invalid or expired token"}` | Токен недействителен |

---

#### `POST /mail/session`

Регистрирует сессию на конкретный адрес.

**Тело запроса:**

```json
{"email": "local@yourdomain.com"}
```

**Ответы:**

| Код | Тело | Условие |
|---|---|---|
| 201 | `{"email": "...", "expires_in_minutes": N}` | Сессия создана |
| 422 | `{"detail": "Email must use domain: <DOMAIN>"}` | Неверный домен |
| 403 | `{"detail": "This address does not belong to your account"}` | Адрес чужой |
| 401 | `{"detail": "Invalid or expired token"}` | Токен недействителен |

Администраторы из `ADMIN_IDS` могут регистрировать любой адрес домена.

---

#### `POST /mail/session/random`

Генерирует и регистрирует случайный адрес из множества пользователя.

**Ответы:**

| Код | Тело | Условие |
|---|---|---|
| 201 | `{"email": "...", "expires_in_minutes": N}` | Сессия создана |
| 401 | `{"detail": "Invalid or expired token"}` | Токен недействителен |

---

## Алгоритм выдачи адресов

Каждый пользователь получает **65 536 непересекающихся адресов**, детерминированно вычисляемых из `user_id` без базы данных.

```
inp = user_id × 65536 + nonce   (nonce — случайное 16-битное число)
```

`inp` шифруется 8-раундовой Feistel-сетью с ключом `ENCRYPT_KEY` и кодируется в 7 слогов из алфавита 150 слогов (строка 14–21 символов).

Верификация адреса — расшифровка и проверка `decrypted // 65536 == user_id`.

Общее пространство: `150^7 ≈ 1.7 × 10^15` адресов, максимум ~26 млрд пользователей без коллизий.

---

## Логирование

- **stdout / INFO**: Telegram-апдейты (user_id, имя, контент, время обработки), события SMTP.
- **Файл / WARNING+**: только ошибки и предупреждения.
- Внутренние логи `aiosmtpd` подавляются.
