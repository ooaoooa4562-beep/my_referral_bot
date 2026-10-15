import os
import threading
import telebot
from flask import Flask

from config import BOT_TOKEN
from database import init_db
from handlers import start, my_ref, help


# --- Flask для Render (чтобы сервис не засыпал) ---
app = Flask(__name__)


@app.route("/")
@app.route("/health")
def health():
    return "Bot is running", 200


# --- Инициализация бота ---
bot = telebot.TeleBot(BOT_TOKEN)
start.register(bot)
my_ref.register(bot)
help.register(bot)


def run_bot():
    init_db()
    print("Бот запущен...")
    bot.infinity_polling()


def main():
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
