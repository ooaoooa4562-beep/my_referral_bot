from telebot import types


def register(bot):
    @bot.message_handler(commands=["help"])
    def cmd_help(message: types.Message):
        bot.reply_to(
            message,
            "Доступные команды:\n"
            "/start — начать\n"
            "/my_ref — моя реферальная ссылка",
        )
