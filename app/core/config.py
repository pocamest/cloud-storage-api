from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore", case_sensitive=False
    )

    postgres_user: str = "app"
    postgres_password: str = "change_me"
    postgres_db: str = "cloud_storage"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    redis_password: str = ""
    redis_port: int = 6379
    redis_host: str = "localhost"

    log_level: str = "INFO"

    token_secret_key: str
    token_algorithm: str = "HS256"
    access_token_exp_minutes: int = 15
    refresh_token_exp_days: int = 30

    @property
    def database_url(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.postgres_user,
                password=self.postgres_password,
                host=self.postgres_host,
                port=self.postgres_port,
                path=self.postgres_db,
            )
        )

    @property
    def redis_url(self) -> str:
        return str(
            RedisDsn.build(
                scheme="redis",
                password=self.redis_password,
                host=self.redis_host,
                port=self.redis_port,
            )
        )


settings = Settings()
