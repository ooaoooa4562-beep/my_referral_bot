import time
from telebot import types

from config import ADMIN_IDS
from database import (
    get_stats, get_top_referrers, get_recent_users,
    find_user, get_all_user_ids,
    ban_user, unban_user, delete_user,
)
from keyboards.admin import (
    admin_menu, back_button, cancel_button,
    confirm_broadcast_button, user_actions_keyboard, confirm_delete_keyboard,
)


_admin_state = {}


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def register(bot):

    @bot.message_handler(commands=["admin"])
    def cmd_admin(message: types.Message):
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "⛔ У вас нет доступа.")
            return
        bot.send_message(
            message.chat.id,
            "🛠 <b>Админ-панель</b>\n\nВыберите раздел:",
            parse_mode="HTML",
            reply_markup=admin_menu(),
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin:"))
    def admin_callback(call: types.CallbackQuery):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "Нет доступа")
            return

        action = call.data.split(":", 1)[1]
        chat_id = call.message.chat.id
        msg_id = call.message.message_id

        if action == "close":
            bot.delete_message(chat_id, msg_id)
            bot.answer_callback_query(call.id)
            return

        if action == "menu":
            _admin_state.pop(call.from_user.id, None)
            bot.edit_message_text(
                "🛠 <b>Админ-панель</b>\n\nВыберите раздел:",
                chat_id, msg_id, parse_mode="HTML", reply_markup=admin_menu(),
            )
            bot.answer_callback_query(call.id)
            return

        if action == "stats":
            s = get_stats()
            text = (
                "📊 <b>Статистика бота</b>\n\n"
                f"👥 Всего пользователей: <b>{s['total']}</b>\n"
                f"🔗 Пришли по реф-ссылке: <b>{s['referred']}</b>\n"
                f"⭐ Активных рефереров: <b>{s['referrers']}</b>\n"
                f"🆕 Новых за 24 часа: <b>{s['last_24h']}</b>\n"
                f"🚫 Забанено: <b>{s['banned']}</b>"
            )
            bot.edit_message_text(
                text, chat_id, msg_id, parse_mode="HTML", reply_markup=back_button(),
            )

        elif action == "top":
            rows = get_top_referrers(10)
            if not rows:
                text = "🏆 Пока никто никого не пригласил."
            else:
                lines = ["🏆 <b>Топ-10 рефереров</b>\n"]
                for i, u in enumerate(rows, 1):
                    name = u["first_name"] or "—"
                    uname = f"@{u['username']}" if u["username"] else ""
                    lines.append(f"{i}. {name} {uname} — <b>{u['referrals_count']}</b>")
                text = "\n".join(lines)
            bot.edit_message_text(
                text, chat_id, msg_id, parse_mode="HTML", reply_markup=back_button(),
            )

        elif action == "recent":
            rows = get_recent_users(20)
            lines = ["👥 <b>Последние 20 пользователей</b>\n"]
            for u in rows:
                name = u["first_name"] or "—"
                uname = f"@{u['username']}" if u["username"] else "—"
                ban_mark = " 🚫" if u["is_banned"] else ""
                lines.append(
                    f"• {name} ({uname}){ban_mark} — код <code>{u['referral_code']}</code>, "
                    f"пригласил: {u['referrals_count']}"
                )
            bot.edit_message_text(
                "\n".join(lines), chat_id, msg_id, parse_mode="HTML",
                reply_markup=back_button(),
            )

        elif action == "find":
            _admin_state[call.from_user.id] = "find"
            bot.edit_message_text(
                "🔍 Введите <b>Telegram ID</b> или <b>@username</b> пользователя:",
                chat_id, msg_id, parse_mode="HTML", reply_markup=cancel_button(),
            )

        elif action == "broadcast":
            _admin_state[call.from_user.id] = "broadcast"
            bot.edit_message_text(
                "📢 Отправьте текст рассылки.\nОн уйдёт всем незабаненным пользователям.",
                chat_id, msg_id, parse_mode="HTML", reply_markup=cancel_button(),
            )

        elif action == "broadcast_confirm":
            data = _admin_state.get(call.from_user.id)
            text = data.get("text") if isinstance(data, dict) else None
            if not text:
                bot.answer_callback_query(call.id, "Текст потерян, попробуйте снова")
                return
            _admin_state.pop(call.from_user.id, None)
            bot.edit_message_text("📢 Рассылка запущена...", chat_id, msg_id)

            ids = get_all_user_ids(include_banned=False)
            ok, fail = 0, 0
            for uid in ids:
                try:
                    bot.send_message(uid, text)
                    ok += 1
                    time.sleep(0.05)
                except Exception:
                    fail += 1
            bot.send_message(
                chat_id,
                f"✅ Рассылка завершена.\nДоставлено: {ok}\nНе доставлено: {fail}",
            )

        elif action.startswith("ban:"):
            uid = int(action.split(":")[1])
            if ban_user(uid):
                bot.answer_callback_query(call.id, "🚫 Пользователь забанен")
                bot.edit_message_reply_markup(
                    chat_id, msg_id,
                    reply_markup=user_actions_keyboard(uid, banned=True),
                )
            else:
                bot.answer_callback_query(call.id, "❌ Не удалось")

        elif action.startswith("unban:"):
            uid = int(action.split(":")[1])
            if unban_user(uid):
                bot.answer_callback_query(call.id, "✅ Разбанен")
                bot.edit_message_reply_markup(
                    chat_id, msg_id,
                    reply_markup=user_actions_keyboard(uid, banned=False),
                )
            else:
                bot.answer_callback_query(call.id, "❌ Не удалось")

        elif action.startswith("delete:"):
            uid = int(action.split(":")[1])
            bot.edit_message_text(
                f"🗑 Удалить пользователя <code>{uid}</code> из базы?\n"
                f"<b>Это действие необратимо.</b>",
                chat_id, msg_id, parse_mode="HTML",
                reply_markup=confirm_delete_keyboard(uid),
            )

        elif action.startswith("delete_confirm:"):
            uid = int(action.split(":")[1])
            if delete_user(uid):
                bot.edit_message_text(
                    f"✅ Пользователь <code>{uid}</code> удалён.",
                    chat_id, msg_id, parse_mode="HTML",
                    reply_markup=back_button(),
                )
            else:
                bot.answer_callback_query(call.id, "❌ Не удалось удалить")

        bot.answer_callback_query(call.id)

    @bot.message_handler(
        func=lambda m: _admin_state.get(m.from_user.id) is not None
                      and is_admin(m.from_user.id)
    )
    def handle_admin_text(message: types.Message):
        state = _admin_state.get(message.from_user.id)
        text = (message.text or "").strip()

        if state == "find":
            _admin_state.pop(message.from_user.id, None)
            user = find_user(text)
            if not user:
                bot.send_message(message.chat.id, "❌ Пользователь не найден.")
                return

            banned_status = "🚫 Забанен" if user["is_banned"] else "✅ Активен"
            info = (
                f"🔍 <b>Найден пользователь</b>\n\n"
                f"ID: <code>{user['telegram_id']}</code>\n"
                f"Имя: {user['first_name'] or '—'}\n"
                f"Username: @{user['username'] or '—'}\n"
                f"Реф-код: <code>{user['referral_code']}</code>\n"
                f"Пригласил: <b>{user['referrals_count']}</b>\n"
                f"Его пригласил ID: {user['referred_by'] or '—'}\n"
                f"Статус: {banned_status}"
            )
            bot.send_message(
                message.chat.id, info, parse_mode="HTML",
                reply_markup=user_actions_keyboard(
                    user["telegram_id"], banned=user["is_banned"]
                ),
            )

        elif state == "broadcast":
            _admin_state[message.from_user.id] = {"text": text}
            bot.send_message(
                message.chat.id,
                f"📢 <b>Проверьте текст:</b>\n\n{text}\n\nОтправляем?",
                parse_mode="HTML",
                reply_markup=confirm_broadcast_button(),
  )
