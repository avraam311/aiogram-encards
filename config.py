import os
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())


class Config:
    def __init__(self):
        self.telegram_api_token: str = os.getenv('TELEGRAM_API_TOKEN')
        self.telegram_admin_id: int = int(os.getenv('TELEGRAM_ADMIN_ID'))
        self.payments_token: str = os.getenv('PAYMENTS_TOKEN')
        self.psql_url: str = os.getenv('PSQL_URL')
        self.psql_user: str = os.getenv('PSQL_USER')
        self.psql_password: str = os.getenv('PSQL_PASSWORD')
        self.psql_host: str = os.getenv('PSQL_HOST')
        self.psql_port: int = int(os.getenv('PSQL_PORT'))
        self.psql_db: str = os.getenv('PSQL_DB')
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
        if not self.psql_user:
            raise ValueError("PSQL_USER не установлен")
        if not self.psql_password:
            raise ValueError("PSQL_PASSWORD не установлен")
        if not self.psql_host:
            raise ValueError("PSQL_HOST не установлен")
        if not self.psql_port:
            raise ValueError("PSQL_PORT не установлен")
        if not self.psql_db:
            raise ValueError("PSQL_DB не установлен")
        if not self.redis_username:
            raise ValueError("REDIS_USERNAME не установлен")
        if not self.redis_password:
            raise ValueError("REDIS_PASSWORD не установлен")
        if not self.redis_host:
            raise ValueError("REDIS_HOST не установлен")
        if not self.redis_port:
            raise ValueError("REDIS_PORT не установлен")
