import os
from logging import config as logging_config

from core.logger import LOGGING

from pydantic import BaseSettings, PostgresDsn, Field

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)

# Название проекта. Используется в Swagger-документации
PROJECT_NAME = os.getenv('PROJECT_NAME', 'short_links')
PROJECT_HOST = os.getenv('PROJECT_HOST', '127.0.0.1')
PROJECT_PORT = int(os.getenv('PROJECT_PORT', '8080'))

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AppSettings(BaseSettings):
    app_title: str = "ShortLinksApp"
    database_dsn: PostgresDsn = Field(
        "postgresql+asyncpg://ypuser:yppass@localhost:5432/short_links",
        env='DATABASE_DSN',
    )

    project_host: str = PROJECT_HOST
    project_port: int = PROJECT_PORT

    class Config:
        env_file = '.env'


app_settings = AppSettings()

PROJECT_URL = f'http://{app_settings.project_host}:{app_settings.project_port}/api/v1/'
