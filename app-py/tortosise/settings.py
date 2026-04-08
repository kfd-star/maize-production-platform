import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _env_flag(name: str, default: str = "False") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


TORTOISE_ORM = {
    "connections": {
        "default": {
            # 'engine': 'tortoise.backends.asyncpg',  PostgreSQL
            "engine": "tortoise.backends.mysql",  # MySQL or Mariadb
            "credentials": {
                "host": os.getenv("DB_HOST", "127.0.0.1"),
                "port": os.getenv("DB_PORT", "3306"),
                "user": os.getenv("DB_USER", "root"),
                "password": os.getenv("DB_PASSWORD", ""),
                "database": os.getenv("DB_NAME", "cornpy"),
                "minsize": 1,
                "maxsize": 5,
                "charset": "utf8mb4",
                "echo": _env_flag("DB_ECHO", "True"),
            },
        },
    },
    "apps": {
        "models": {
            "models": ["models.user", "aerich.models"],
            "default_connection": "default",
        }
    },
    "use_tz": False,
    "timezone": "Asia/Shanghai",
}
