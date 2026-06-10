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
| `POST` | `/mail/session` | Зарегистрировать конкретный адрес |
| `POST` | `/mail/session/random` | Зарегистрировать случайный адрес |
| `DELETE` | `/mail/session` | Остановить активную сессию |
| `GET` | `/mail/poll` | Ожидать входящее письмо (long poll) |
