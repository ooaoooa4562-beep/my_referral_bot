import os
from urllib.parse import urlparse, urlunparse, parse_qs

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# ID админов через запятую: "123456789,987654321"
_admin_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in _admin_raw.split(",") if x.strip().isdigit()]

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL не найден в переменных окружения")


def _clean_db_url(url: str) -> str:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    allowed = {"sslmode": qs["sslmode"]} if "sslmode" in qs else {}
    new_query = "&".join(f"{k}={v[0]}" for k, v in allowed.items())
    cleaned = urlunparse(parsed._replace(query=new_query))
    if cleaned.startswith("postgres://"):
        cleaned = cleaned.replace("postgres://", "postgresql://", 1)
    return cleaned


DB_URL = _clean_db_url(DATABASE_URL)
