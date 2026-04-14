from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel

ROOT_APP_PATH = Path(__file__).parent.parent.resolve()


class DatabaseConfig(BaseModel):
    dsn: str
    min_pool_size: int
    max_pool_size: int


class RabbitSettings(BaseModel):
    dsn: str


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            ROOT_APP_PATH / '.env.default',
            ROOT_APP_PATH / '.env',
        ),
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        extra='ignore',
    )

    # PostgreSQL
    psql_db: DatabaseConfig

    # RabbitMQ
    rabbitmq: RabbitSettings

    # Auth
    api_key: str

    # Outbox poller
    outbox_poll_interval: float = 2.0


settings = AppSettings()
