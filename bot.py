import telebot
from telebot import types

from config import BOT_TOKEN
from database import (
    init_db,
    get_user,
    create_user,
    get_user_by_code,
    set_referrer,
    get_referrals_count,
)

bot = telebot.TeleBot(BOT_TOKEN)


def extract_payload(text: str):
    """Достаёт параметр из /start payload."""
    parts = text.split(maxsplit=1)
    return parts[1] if len(parts) > 1 else None


@bot.message_handler(commands=["start"])
def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""

    # 1. Регистрируем/обновляем пользователя, получаем его реф-код
    referral_code = create_user(user_id, username, first_name)

    # 2. Обрабатываем реферальный payload
    payload = extract_payload(message.text or "")
    if payload:
        referrer_id = get_user_by_code(payload)
        if referrer_id:
            success = set_referrer(user_id, referrer_id)
            if success:
                try:
                    bot.send_message(
                        referrer_id,
                        "🎉 По вашей ссылке пришёл новый пользователь!",
                    )
                except Exception:
                    pass  # реферер мог заблокировать бота

    # 3. Приветствие + реферальная ссылка
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


@bot.message_handler(commands=["my_ref"])
def cmd_my_ref(message: types.Message):
    user = get_user(message.from_user.id)
    if not user:
        bot.reply_to(message, "Сначала напишите /start")
        return

    bot_username = bot.get_me().username
    ref_link = f"https://t.me/{bot_username}?start={user['referral_code']}"

    share_text = "Заходи в бота по моей ссылке!"
    share_url = f"https://t.me/share/url?url={ref_link}&text={share_text}"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📤 Поделиться", url=share_url))

    bot.send_message(
        message.chat.id,
        f"Ваша ссылка:\n{ref_link}\n\n"
        f"Приглашено: {user['referrals_count']} чел.",
        reply_markup=markup,
    )


@bot.message_handler(commands=["help"])
def cmd_help(message: types.Message):
    bot.reply_to(
        message,
        "Доступные команды:\n"
        "/start — начать\n"
        "/my_ref — моя реферальная ссылка",
    )


if __name__ == "__main__":
    init_db()
    print("Бот запущен...")
    bot.infinity_polling()
