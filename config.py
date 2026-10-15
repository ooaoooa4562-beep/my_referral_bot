import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Путь к SQLite-файлу. На Render можно переопределить через переменную окружения,
# указав путь внутри постоянного диска, например: /data/bot.db
DB_PATH = os.getenv("DB_PATH", "bot.db")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")
