import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = "bot.db"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")
