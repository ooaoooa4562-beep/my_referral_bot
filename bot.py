import os
import threading
import telebot
from flask import Flask

from config import BOT_TOKEN
from database import init_db, is_banned
from handlers import start, my_ref, help, admin, menu_buttons


app = Flask(__name__)


@app.route("/")
@app.route("/health")
def health():
    return "Bot is running", 200


bot = telebot.TeleBot(BOT_TOKEN)


def run_bot():
    init_db()
    print("Бот запущен...")
    bot.infinity_polling()


def main():
    start.register(bot)
    my_ref.register(bot)
    help.register(bot)
    admin.register(bot)
    menu_buttons.register(bot)

    @bot.message_handler(
        func=lambda m: is_banned(m.from_user.id),
        content_types=["text"],
    )
    def block_banned(message):
        return

    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
