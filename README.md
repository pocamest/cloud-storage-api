# Cloud Storage API

API для облачного хранилища. Спроектирован в рамках async-first.

Демо (Swagger): http://87.242.85.167

## Стек:

- **Core:** Python, FastAPI, Uvicorn
- **Databases:** PostgreSQL 15+, Redis
-  **ORM & Migrations:** SQLAlchemy, Alembic
- **Storage:** MinIO, aiobotocore
- **Dev Tools:** Docker Compose, uv, ruff, mypy, pre-commit

## Начало работы

### Предварительные требования
- uv
- Docker

### Подготовка проекта

1. Клонирование репозитория:
    ```bash
    git clone https://github.com/pocamest/cloud-storage-api.git
    cd cloud-storage-api
    ```
2. На основе примера заполнить `.env`:
    ```bash
    cp .env.example .env
    ```

### Локальная разработка

Инфраструктура приложения - PostgreSQL, Redis и Minio (с созданием бакета) запускаются в Docker, а код работает локально на хосте с помощью uv.

1. Запуск инфраструктуры:
    ```bash
    docker compose up -d
    ```

2. Установка зависимостей:
    ```bash
    uv sync
    ```

3. Установка pre-commit хуков:
    ```bash
    uv run pre-commit install
    ```

4. Применение миграций:
    ```bash
    uv run alembic upgrade head
    ```

5. Запуск сервера:
    ```bash
    uv run uvicorn app.main:app --reload
    ```

### Деплой

Для деплоя используется отдельная конфигурация, где вся инфраструктура и само приложение (включая применение миграций) запускаются в Docker.

1. Запуск приложения:
    ```bash
    docker compose -f docker-compose.prod.yaml up -d --build
    ```
