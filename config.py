import os
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())


class Config:
    def __init__(self):
        self.telegram_api_token: str = os.getenv('TELEGRAM_API_TOKEN')
        self.telegram_admin_id: int = int(os.getenv('TELEGRAM_ADMIN_ID'))
        self.payments_token: str = os.getenv('PAYMENTS_TOKEN')
        self.psql_url: str = os.getenv('PSQL_URL')
        self.redis_username: str = os.getenv('REDIS_USERNAME')
        self.redis_password: str = os.getenv('REDIS_PASSWORD')
        self.redis_host: str = os.getenv('REDIS_HOST')
        self.redis_port: int = int(os.getenv('REDIS_PORT'))

    def validate(self) -> None:
        if not self.telegram_api_token:
            raise ValueError("TELEGRAM_API_TOKEN не установлен")
        if not self.telegram_admin_id:
            raise ValueError("TELEGRAM_ADMIN_ID не установлен")
        if not self.payments_token:
            raise ValueError("PAYMENTS_TOKEN не установлен")
        if not self.psql_url:
            raise ValueError("PSQL_URL не установлен")
        if not self.redis_username:
            raise ValueError("REDIS_USERNAME не установлен")
        if not self.redis_password:
            raise ValueError("REDIS_PASSWORD не установлен")
        if not self.redis_host:
            raise ValueError("REDIS_HOST не установлен")
        if not self.redis_port:
            raise ValueError("REDIS_PORT не установлен")
