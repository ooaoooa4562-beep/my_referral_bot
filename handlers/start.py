from telebot import types

from database import (
    create_user, get_user_by_code, set_referrer, get_referrals_count, is_banned,
)
from keyboards.main import main_reply_menu, start_inline_menu


def extract_payload(text: str):
    parts = text.split(maxsplit=1)
    return parts[1] if len(parts) > 1 else None


def get_level(count: int) -> str:
    if count >= 30:
        return "🥇 Золото"
    elif count >= 15:
        return "🥈 Серебро"
    elif count >= 5:
        return "🥉 Бронза"
    return "🌱 Новичок"


def register(bot):
    @bot.message_handler(commands=["start"])
    def cmd_start(message: types.Message):
        if is_banned(message.from_user.id):
            return

        user_id = message.from_user.id
        username = message.from_user.username or ""
        first_name = message.from_user.first_name or ""

        referral_code = create_user(user_id, username, first_name)

        payload = extract_payload(message.text or "")
        if payload:
            referrer_id = get_user_by_code(payload)
            if referrer_id and set_referrer(user_id, referrer_id):
                # Уведомление пригласившему
                count = get_referrals_count(referrer_id)
                level = get_level(count)
                try:
                    if count in (5, 15, 30):
                        bot.send_message(
                            referrer_id,
                            f"🎉 <b>Поздравляем! Новый уровень!</b>\n\n"
                            f"Вы пригласили {count} человек и получили статус: <b>{level}</b>!",
                            parse_mode="HTML"
                        )
                    else:
                        bot.send_message(
                            referrer_id,
                            f"🎉 По вашей ссылке пришёл новый пользователь!\n"
                            f"Всего приглашено: <b>{count}</b> чел.\nСтатус: {level}",
                            parse_mode="HTML"
                        )
                except Exception:
                    pass

        bot_username = bot.get_me().username
        ref_link = f"https://t.me/{bot_username}?start={referral_code}"
        count = get_referrals_count(user_id)
        level = get_level(count)

        text = (
            f"👋 Привет, <b>{first_name}</b>!\n\n"
            f"Твой текущий статус: <b>{level}</b> (приглашено: {count})\n\n"
            f"Приглашай друзей и получай бонусы! За каждого друга — плюс к твоему уровню.\n\n"
            f"Твоя ссылка для приглашений:\n<code>{ref_link}</code>"
        )
        
        bot.send_message(
            user_id, text, parse_mode="HTML",
            reply_markup=main_reply_menu()
        )
        bot.send_message(
            user_id, "Выбери действие на клавиатуре ниже или нажми кнопку:",
            reply_markup=start_inline_menu()
                        )
