from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore", case_sensitive=False
    )

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int

    redis_password: str
    redis_port: int
    redis_host: str

    log_level: str

    token_secret_key: str
    token_algorithm: str
    access_token_exp_minutes: int
    refresh_token_exp_days: int

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
