from telebot import types
from database import get_user, is_banned, get_users_invited_by


def register(bot):
    @bot.message_handler(func=lambda m: m.text == "🏆 Мои успехи")
    def my_progress(message: types.Message):
        if is_banned(message.from_user.id):
            return
        user = get_user(message.from_user.id)
        if not user:
            bot.reply_to(message, "Сначала напишите /start")
            return

        count = user["referrals_count"]
        if count >= 30:
            level = "🥇 Золото"
        elif count >= 15:
            level = "🥈 Серебро"
        elif count >= 5:
            level = "🥉 Бронза"
        else:
            level = "🌱 Новичок"

        text = (
            f"🏆 <b>Твои успехи</b>\n\n"
            f"Статус: <b>{level}</b>\n"
            f"Приглашено: <b>{count}</b> чел.\n\n"
            f"<b>Уровни:</b>\n"
            f"🥉 Бронза — 5 друзей\n"
            f"🥈 Серебро — 15 друзей\n"
            f"🥇 Золото — 30 друзей"
        )
        bot.send_message(message.chat.id, text, parse_mode="HTML")

    @bot.message_handler(func=lambda m: m.text == "👥 Мои друзья")
    def my_friends(message: types.Message):
        if is_banned(message.from_user.id):
            return
        friends = get_users_invited_by(message.from_user.id)
        if not friends:
            bot.send_message(message.chat.id, "Ты пока никого не пригласил. Скинь свою ссылку друзьям!")
            return

        lines = ["👥 <b>Твои друзья:</b>\n"]
        for i, f in enumerate(friends[:20], 1):
            name = f["first_name"] or "—"
            uname = f"@{f['username']}" if f["username"] else ""
            lines.append(f"{i}. {name} {uname}")

        if len(friends) > 20:
            lines.append(f"\n... и ещё {len(friends) - 20} чел.")

        bot.send_message(message.chat.id, "\n".join(lines), parse_mode="HTML")

    @bot.message_handler(func=lambda m: m.text == "ℹ️ Как это работает")
    @bot.callback_query_handler(func=lambda call: call.data == "menu:help")
    def how_it_works(event):
        text = (
            "ℹ️ <b>Как это работает:</b>\n\n"
            "1. Ты получаешь свою уникальную ссылку.\n"
            "2. Отправляешь её друзьям.\n"
            "3. Друг переходит по ссылке и запускает бота.\n"
            "4. Тебе засчитывается +1 приглашённый.\n\n"
            "За приглашённых друзей ты получаешь статусы:\n"
            "🥉 Бронза — 5 друзей\n"
            "🥈 Серебро — 15 друзей\n"
            "🥇 Золото — 30 друзей\n\n"
            "Чем больше друзей, тем выше твой статус!"
        )
        if isinstance(event, types.CallbackQuery):
            bot.answer_callback_query(event.id)
            bot.send_message(event.message.chat.id, text, parse_mode="HTML")
        else:
            bot.send_message(event.chat.id, text, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda call: call.data == "menu:my_ref")
    def inline_my_ref(call: types.CallbackQuery):
        bot.answer_callback_query(call.id)
        user = get_user(call.from_user.id)
        if not user:
            bot.send_message(call.message.chat.id, "Сначала напишите /start")
            return
        bot_username = bot.get_me().username
        ref_link = f"https://t.me/{bot_username}?start={user['referral_code']}"
        bot.send_message(
            call.message.chat.id,
            f"🔗 Твоя ссылка:\n<code>{ref_link}</code>",
            parse_mode="HTML",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("📤 Поделиться", url=f"https://t.me/share/url?url={ref_link}")
            )
    )
