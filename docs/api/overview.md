# REST API

Интерактивная документация: `https://<API_HOST>:<API_PORT>/docs`

Аутентификация — Bearer JWT, получить через `/apikey` в Telegram.

```
Authorization: Bearer <token>
```

## Эндпоинты

| Метод | Путь | Действие |
|---|---|---|
| `GET` | `/mail/session` | Получить активную сессию |
| `POST` | `/mail/session` | Зарегистрировать адрес |
| `POST` | `/mail/session/random` | Зарегистрировать случайный адрес |
| `GET` | `/mail/poll` | Ожидать входящее письмо (long poll) |
