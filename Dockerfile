FROM ghcr.io/astral-sh/uv:bookworm-slim

WORKDIR /app

# TODO: рассмотреть кэширование для ускорения сборки
COPY . .
RUN uv sync --frozen --no-dev
