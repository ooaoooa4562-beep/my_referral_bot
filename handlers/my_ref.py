from telebot import types

from database import get_user, is_banned
from keyboards.main import share_button


def get_level_info(count: int):
    if count >= 30:
        return "🥇 Золото", "Максимальный уровень! Ты легенда!"
    elif count >= 15:
        return "🥈 Серебро", f"До Золота осталось {30 - count} чел."
    elif count >= 5:
        return "🥉 Бронза", f"До Серебра осталось {15 - count} чел."
    else:
        return "🌱 Новичок", f"До Бронзы осталось {5 - count} чел."


def register(bot):
    @bot.message_handler(commands=["my_ref"])
    @bot.message_handler(func=lambda m: m.text == "🔗 Моя ссылка")
    def cmd_my_ref(message: types.Message):
        if is_banned(message.from_user.id):
            return

        user = get_user(message.from_user.id)
        if not user:
            bot.reply_to(message, "Сначала напишите /start")
            return

        bot_username = bot.get_me().username
        ref_link = f"https://t.me/{bot_username}?start={user['referral_code']}"
        count = user['referrals_count']
        level, progress = get_level_info(count)

        text = (
            f"🔗 <b>Твоя реферальная ссылка:</b>\n"
            f"<code>{ref_link}</code>\n\n"
            f"🏅 Твой статус: <b>{level}</b>\n"
            f"👥 Приглашено друзей: <b>{count}</b>\n"
            f"📈 {progress}"
        )

        bot.send_message(
            message.chat.id, text, parse_mode="HTML",
            reply_markup=share_button(ref_link)
        )
