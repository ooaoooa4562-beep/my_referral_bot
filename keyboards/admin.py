from telebot import types


def admin_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin:stats"),
        types.InlineKeyboardButton("🏆 Топ рефереров", callback_data="admin:top"),
    )
    markup.add(
        types.InlineKeyboardButton("👥 Последние юзеры", callback_data="admin:recent"),
        types.InlineKeyboardButton("🔍 Найти юзера", callback_data="admin:find"),
    )
    markup.add(
        types.InlineKeyboardButton("📢 Рассылка", callback_data="admin:broadcast"),
        types.InlineKeyboardButton("⬅️ Закрыть", callback_data="admin:close"),
    )
    return markup


def back_button() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="admin:menu"))
    return markup


def cancel_button() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❌ Отмена", callback_data="admin:menu"))
    return markup


def confirm_broadcast_button() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Отправить", callback_data="admin:broadcast_confirm"),
        types.InlineKeyboardButton("❌ Отмена", callback_data="admin:menu"),
    )
    return markup


def user_actions_keyboard(telegram_id: int, banned: bool) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)

    if banned:
        markup.add(types.InlineKeyboardButton(
            "✅ Разбанить", callback_data=f"admin:unban:{telegram_id}"))
    else:
        markup.add(types.InlineKeyboardButton(
            "🚫 Забанить", callback_data=f"admin:ban:{telegram_id}"))

    markup.add(types.InlineKeyboardButton(
        "🗑 Удалить", callback_data=f"admin:delete:{telegram_id}"))
    markup.add(types.InlineKeyboardButton(
        "⬅️ Назад", callback_data="admin:menu"))
    return markup


def confirm_delete_keyboard(telegram_id: int) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            "✅ Да, удалить", callback_data=f"admin:delete_confirm:{telegram_id}"),
        types.InlineKeyboardButton("❌ Отмена", callback_data="admin:menu"),
    )
    return markup


def skip_photo_keyboard() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "➡️ Без фото", callback_data="admin:broadcast_skip_photo"))
    markup.add(types.InlineKeyboardButton(
        "❌ Отмена", callback_data="admin:menu"))
    return markup
