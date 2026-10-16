from telebot import types

from database import is_banned


def register(bot):
    @bot.message_handler(commands=["help"])
    def cmd_help(message: types.Message):
        if is_banned(message.from_user.id):
            return

        bot.reply_to(
            message,
            "Доступные команды:\n"
            "/start — начать\n"
            "/my_ref — моя реферальная ссылка",
        )
