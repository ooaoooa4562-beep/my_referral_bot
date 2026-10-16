from telebot import types


def share_button(ref_link: str) -> types.InlineKeyboardMarkup:
    share_text = "Заходи в бота по моей ссылке!"
    share_url = f"https://t.me/share/url?url={ref_link}&text={share_text}"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📤 Поделиться", url=share_url))
    return markup
