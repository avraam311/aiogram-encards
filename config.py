import os
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())


class Config:
    def __init__(self):
        self.telegram_api_token: str = os.getenv('TELEGRAM_API_TOKEN')
        self.telegram_admin_id: int = int(os.getenv('TELEGRAM_ADMIN_ID'))
        self.payments_token: str = os.getenv('PAYMENTS_TOKEN')
        self.postgres_url: str = os.getenv('POSTGRES_URL')
        self.postgres_user: str = os.getenv('POSTGRES_USER')
        self.postgres_password: str = os.getenv('POSTGRES_PASSWORD')
        self.postgres_host: str = os.getenv('POSTGRES_HOST')
        self.postgres_port: int = int(os.getenv('POSTGRES_PORT'))
        self.postgres_db: str = os.getenv('POSTGRES_DB')
        self.redis_username: str = os.getenv('REDIS_USERNAME')
        self.redis_password: str = os.getenv('REDIS_PASSWORD')
        self.redis_host: str = os.getenv('REDIS_HOST')
        self.redis_port: int = int(os.getenv('REDIS_PORT'))
        self.redis_db: int = int(os.getenv('REDIS_DB'))

    def validate(self) -> None:
        if not self.telegram_api_token:
            raise ValueError("TELEGRAM_API_TOKEN не установлен")
        if not self.telegram_admin_id:
            raise ValueError("TELEGRAM_ADMIN_ID не установлен")
        if not self.payments_token:
            raise ValueError("PAYMENTS_TOKEN не установлен")
        if not self.postgres_url:
            raise ValueError("POSTGRES_URL не установлен")
        if not self.postgres_user:
            raise ValueError("POSTGRES_USER не установлен")
        if not self.postgres_password:
            raise ValueError("POSTGRES_PASSWORD не установлен")
        if not self.postgres_host:
            raise ValueError("POSTGRES_HOST не установлен")
        if not self.postgres_port:
            raise ValueError("POSTGRES_PORT не установлен")
        if not self.postgres_db:
            raise ValueError("POSTGRES_DB не установлен")
        if not self.redis_username:
            raise ValueError("REDIS_USERNAME не установлен")
        if not self.redis_password:
            raise ValueError("REDIS_PASSWORD не установлен")
        if not self.redis_host:
            raise ValueError("REDIS_HOST не установлен")
        if not self.redis_port:
            raise ValueError("REDIS_PORT не установлен")
        if not self.redis_db:
            raise ValueError("REDIS_DB не установлен")
