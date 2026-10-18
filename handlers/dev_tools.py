from telebot import types
from config import DEV_IDS
from database import add_tokens, get_tokens, create_promocode


def register(bot):
    @bot.message_handler(commands=["give_tokens"])
    def cmd_give_tokens(message: types.Message):
        if message.from_user.id not in DEV_IDS:
            return

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

    @bot.message_handler(commands=["create_promo"])
    def cmd_create_promo(message: types.Message):
        if message.from_user.id not in DEV_IDS:
            return
        
        # Формат: /create_promo SUMMER 5 100
        args = message.text.split()
        if len(args) < 4:
            bot.reply_to(
                message, 
                "⚠️ Формат: <code>/create_promo КОД НАГРАДА ЛИМИТ</code>\n"
                "Пример: <code>/create_promo SUMMER 5 100</code>", 
                parse_mode="HTML"
            )
            return
            
        code = args[1]
        reward = int(args[2])
        limit = int(args[3])
        
        create_promocode(code, reward, limit)
        bot.reply_to(
            message, 
            f"✅ Промокод <code>{code}</code> создан!\n"
            f"Награда: {reward} токенов.\n"
            f"Лимит: {limit} активаций.", 
            parse_mode="HTML"
    )
