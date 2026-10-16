from telebot import types

from database import get_user, is_banned
from keyboards import share_button


def register(bot):
    @bot.message_handler(commands=["my_ref"])
    def cmd_my_ref(message: types.Message):
        if is_banned(message.from_user.id):
            return

        user = get_user(message.from_user.id)
        if not user:
            bot.reply_to(message, "Сначала напишите /start")
            return

        bot_username = bot.get_me().username
        ref_link = f"https://t.me/{bot_username}?start={user['referral_code']}"

        bot.send_message(
            message.chat.id,
            f"Ваша ссылка:\n{ref_link}\n\n"
            f"Приглашено: {user['referrals_count']} чел.",
            reply_markup=share_button(ref_link),
        )
