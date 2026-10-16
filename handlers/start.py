from telebot import types

from database import (
    create_user, get_user_by_code, set_referrer, get_referrals_count, is_banned,
)


def extract_payload(text: str):
    parts = text.split(maxsplit=1)
    return parts[1] if len(parts) > 1 else None


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
            if referrer_id:
                if set_referrer(user_id, referrer_id):
                    try:
                        bot.send_message(
                            referrer_id,
                            "🎉 По вашей ссылке пришёл новый пользователь!",
                        )
                    except Exception:
                        pass

        bot_username = bot.get_me().username
        ref_link = f"https://t.me/{bot_username}?start={referral_code}"

        text = (
            f"Привет, {first_name}!\n\n"
            f"Ваша реферальная ссылка:\n{ref_link}\n\n"
            f"Приглашено: {get_referrals_count(user_id)} чел.\n\n"
            f"Команды:\n"
            f"/my_ref — показать ссылку\n"
            f"/help — помощь"
        )
        bot.send_message(user_id, text)
