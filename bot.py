import telebot

from config import BOT_TOKEN
from database import init_db
from handlers import start, my_ref, help


def main():
    bot = telebot.TeleBot(BOT_TOKEN)

    start.register(bot)
    my_ref.register(bot)
    help.register(bot)

    init_db()
    print("Бот запущен...")
    bot.infinity_polling()


if __name__ == "__main__":
    main()
