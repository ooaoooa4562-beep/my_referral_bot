from telebot import types


def main_reply_menu() -> types.ReplyKeyboardMarkup:
    """Постоянные кнопки внизу чата."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🔗 Моя ссылка"),
        types.KeyboardButton("🏆 Мои успехи"),
    )
    markup.add(
        types.KeyboardButton("👥 Мои друзья"),
        types.KeyboardButton("ℹ️ Как это работает"),
    )
    return markup


def share_button(ref_link: str) -> types.InlineKeyboardMarkup:
    share_text = "Заходи в бота по моей ссылке и получай бонусы!"
    share_url = f"https://t.me/share/url?url={ref_link}&text={share_text}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📤 Поделиться с друзьями", url=share_url))
    return markup


def start_inline_menu() -> types.InlineKeyboardMarkup:
    """Кнопки под приветствием."""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔗 Получить мою ссылку", callback_data="menu:my_ref"),
        types.InlineKeyboardButton("ℹ️ Как это работает?", callback_data="menu:help"),
    )
    return markup
