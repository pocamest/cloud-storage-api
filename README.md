# Cloud Storage API

API для облачного хранилища. Спроектирован в рамках модульного монолита и async-first.

## Стэк:

- **Core:** Python, FastAPI, Uvicorn
- **Databases:** PostgreSQL, Redis
-  **ORM & Migrations:** SQLAlchemy, Alembic
- **Storage:** MinIO, aiobotocore
- **Dev Tools:** Docker Compose, uv, ruff, mypy, pre-commit

## Начало работы

### Предварительные требования
- uv
- Docker & Docker Compose

### Настройка локальной разработки

1. Клонирование репозитория:
    ```bash
    git clone https://github.com/pocamest/cloud-storage-api.git
    cd cloud-storage-api
    ```

2. Настройка:
    На основе примера заполнить `.env`.
    ```bash
    cp .env.example .env
    ```

3. Запуск инфраструктуры:
    ```bash
    docker compose up -d
    ```

4. Установка зависимостей:
    ```bash
    uv sync
    ```

5. Применение миграций:
    ```bash
    uv run alembic upgrade head
    ```

6. Запуск сервера:
    ```bash
    uv run uvicorn app.main:app --reload
    ```
