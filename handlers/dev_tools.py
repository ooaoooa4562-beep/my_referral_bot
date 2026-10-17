from telebot import types
from config import DEV_IDS
from database import add_tokens, get_tokens


def register(bot):
    @bot.message_handler(commands=["give_tokens"])
    def cmd_give_tokens(message: types.Message):
        # Проверяем, что команду вызвал разработчик
        if message.from_user.id not in DEV_IDS:
            return  # Обычные юзеры просто игнорируются

        # Разбираем аргументы: /give_tokens 100
        args = message.text.split()
        if len(args) < 2 or not args[1].isdigit():
            bot.reply_to(message, "⚠️ Формат: <code>/give_tokens 100</code>", parse_mode="HTML")
            return

        amount = int(args[1])
        add_tokens(message.from_user.id, amount)
        
        new_balance = get_tokens(message.from_user.id)
        
        bot.reply_to(
            message, 
            f"✅ Успешно начислено <b>{amount}</b> токенов!\n"
            f"Твой текущий баланс: <b>{new_balance}</b>", 
            parse_mode="HTML"
      )
