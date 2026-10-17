from telebot import types

from database import (
    create_user, get_user_by_code, set_referrer, get_referrals_count, is_banned,
    add_tokens, get_tokens
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
                # Начисляем токен пригласившему
                add_tokens(referrer_id, 1)
                
                count = get_referrals_count(referrer_id)
                level = get_level(count)
                try:
                    if count in (5, 15, 30):
                        bot.send_message(
                            referrer_id,
                            f"🎉 <b>Поздравляем! Новый уровень!</b>\n\n"
                            f"Вы пригласили {count} человек и получили статус: <b>{level}</b>!\n"
                            f"Вам начислен <b>1 токен</b>.",
                            parse_mode="HTML"
                        )
                    else:
                        bot.send_message(
                            referrer_id,
                            f"🎉 По вашей ссылке пришёл новый пользователь!\n"
                            f"Вам начислен <b>1 токен</b>.\n"
                            f"Всего приглашено: <b>{count}</b> чел.",
                            parse_mode="HTML"
                        )
                except Exception:
                    pass

        bot_username = bot.get_me().username
        ref_link = f"https://t.me/{bot_username}?start={referral_code}"
        count = get_referrals_count(user_id)
        tokens = get_tokens(user_id)
        level = get_level(count)

        text = (
            f"👋 Привет, <b>{first_name}</b>!\n\n"
            f"🏅 Твой статус: <b>{level}</b>\n"
            f"👥 Приглашено друзей: <b>{count}</b>\n"
            f"🪙 Твои токены: <b>{tokens}</b>\n\n"
            f"Приглашай друзей и получай токены для генерации картинок!\n\n"
            f"Твоя ссылка:\n<code>{ref_link}</code>"
        )
        
        bot.send_message(
            user_id, text, parse_mode="HTML",
            reply_markup=main_reply_menu()
        )
        bot.send_message(
            user_id, "Выбери действие на клавиатуре ниже:",
            reply_markup=start_inline_menu()
                )
