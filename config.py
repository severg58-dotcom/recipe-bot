"""Конфигурация бота. Значения берутся из .env или переменных окружения."""
import os
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH: Path = Path(__file__).parent / ".env"
load_dotenv(ENV_PATH)

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# API рецептов
API_BASE: str = os.getenv("API_BASE", "https://www.themealdb.com/api/json/v1/1")
API_KEY: str = os.getenv("API_KEY", "1")

# Прокси для доступа к api.telegram.org (пусто = не использовать).
# Примеры: socks5://логин:пароль@host:port или http://host:port
# MTProto-прокси из встроенного VPN Telegram НЕ подойдёт!
PROXY_URL: str = os.getenv("PROXY_URL", "")
