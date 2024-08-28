from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import final, Optional


@final
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.dev.env',  # first search .dev.env, then .prod.env
        env_file_encoding='utf-8',
        case_sensitive=False,
    )

    run_type: str = 'dev'
    debug: bool = True

    server_host: str = 'localhost'
    domain: str = 'localhost'
    backend_port: int = 8000
    frontend_port: int = 3000

    # auth config
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SECRET_KEY: str = 'secret'
    ALGORITHM: str = 'HS256'

    # uvicorn config
    host: str = '0.0.0.0'
    port: int = 8000
    reload: bool = True
    workers: int | None = None

    # database config
    db_url: str = f'postgresql+asyncpg://postgres:postgres@{server_host}:5432/postgres'
    db_echo: bool = True
    db_echo_pool: bool = False
    db_pool_size: int = 5
    db_pool_pre_ping: bool = True
    db_max_overflow: int = 10

    redis_broker_url: str = f'redis://{server_host}:6379/0'

    # telegram config
    bot_token: str = ''
    bot_username: str = 'DevBot'
    webapp_username: Optional[str] = 'webapp'
    https_tunnel_url: str = f'https://{domain}'
    # https_tunnel_url: str = ""
    webhook_path: str = f'/webhook'
    webhook_url: str = f'https://{domain}/api/v1{webhook_path}'
    webapp_url: str = f'https://{domain}'
    # Дополнительный токен безопасности для webhook (можно придумать самому)
    tg_secret_token: str = '111'

    # game config
    energy_limit: int = 500
    enterprises_min_slots: int = 10
    enterprises_max_slots: int = 15


@lru_cache()  # get it from memory
def get_settings() -> Settings:
    return Settings()
