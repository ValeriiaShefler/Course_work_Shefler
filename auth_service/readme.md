# Auth Service

## Задачи сервиса
- Регистрация новых пользователей
- Аутентификация (логин)
- Выдача JWT токенов
- Проверка валидности JWT токенов для других сервисов

## API Endpoints
- `POST /register` - регистрация пользователя
- `POST /login` - вход и получение токена
- `GET /verify` - проверка токена (требует Bearer token)
- `GET /health` - проверка работоспособности

## Запуск
```bash
docker build -t auth-service .
docker run -p 8001:8001 --env-file .env auth-service