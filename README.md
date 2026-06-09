# LeetBot

Telegram-бот: принимает входящие письма на временный email-адрес, пересылает пользователю в Telegram как HTML-документ. Встроенный SMTP-сервер, без сторонних почтовых сервисов.

## Установка

```
Python 3.8+
```

```bash
pip install aiogram aiosmtpd email-validator python-dotenv fastapi uvicorn
```

## Запуск

```bash
python main.py
```

SMTP-сервер, Telegram polling и REST API стартуют одновременно в одном asyncio event loop.

## Telegram-команды

| Команда / ввод | Действие                                                  |
|----------------|-----------------------------------------------------------|
| `/random`      | Генерирует новый адрес, активирует сессию                 |
| `/apikey`      | Возвращает JWT-ключ для REST API и ссылку на документацию |
| `localpart`    | Активирует сессию на `localpart@DOMAIN`                   |
| `local@domain` | То же, с явным доменом                                    |

## Документация

- [Архитектура](docs/architecture.md)
- [Конфигурация](docs/configuration.md)
- [REST API](docs/api/overview.md) — [эндпоинты](docs/api/endpoints.md)
- [Алгоритм адресов](docs/address-algorithm.md)
- [Логирование](docs/logging.md)
