import time
from telebot import types

from config import ADMIN_IDS
from database import (
    get_stats, get_top_referrers, find_user, get_all_user_ids,
    ban_user, unban_user, delete_user, get_all_users_paginated
)
from keyboards.admin import (
    admin_menu, back_button, cancel_button, confirm_broadcast_button, 
    skip_photo_keyboard, user_actions_keyboard, confirm_delete_keyboard,
    users_pagination_keyboard
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
            message.chat.id, "🛠 <b>Админ-панель</b>\n\nВыберите раздел:",
            parse_mode="HTML", reply_markup=admin_menu()
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin:"))
    def admin_callback(call: types.CallbackQuery):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "Нет доступа")
            return

        action = call.data.split(":", 1)[1]
        chat_id = call.message.chat.id
        msg_id = call.message.message_id

        if action == "ignore":
            bot.answer_callback_query(call.id)
            return
            
        if action == "close":
            try: bot.delete_message(chat_id, msg_id)
            except Exception: pass
            bot.answer_callback_query(call.id)
            return

        if action == "menu":
            _admin_state.pop(call.from_user.id, None)
            try:
                bot.edit_message_text("🛠 <b>Админ-панель</b>\n\nВыберите раздел:", chat_id, msg_id, parse_mode="HTML", reply_markup=admin_menu())
            except Exception: pass
            bot.answer_callback_query(call.id)
            return

        if action == "stats":
            s = get_stats()
            text = (
                "📊 <b>Общая статистика</b>\n\n"
                f"👥 Всего: <b>{s['total']}</b>\n"
                f"🔗 По реф-ссылке: <b>{s['referred']}</b>\n"
                f"⭐ Рефереров: <b>{s['referrers']}</b>\n"
                f"🆕 За 24 часа: <b>{s['last_24h']}</b>\n"
                f"🚫 Забанено: <b>{s['banned']}</b>"
            )
            try: bot.edit_message_text(text, chat_id, msg_id, parse_mode="HTML", reply_markup=back_button())
            except Exception: pass

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
            try: bot.edit_message_text(text, chat_id, msg_id, parse_mode="HTML", reply_markup=back_button())
            except Exception: pass

        elif action.startswith("users:"):
            page = int(action.split(":")[1])
            data = get_all_users_paginated(page, per_page=10)
            
            lines = [f"👥 <b>Пользователи</b> (стр. {page} из {data['total_pages']}, всего {data['total']})\n"]
            for u in data["users"]:
                name = u["first_name"] or "—"
                uname = f"@{u['username']}" if u["username"] else "—"
                ban_mark = " 🚫" if u["is_banned"] else ""
                lines.append(f"• {name} ({uname}){ban_mark}\nID: <code>{u['telegram_id']}</code>")
            
            try:
                bot.edit_message_text("\n\n".join(lines), chat_id, msg_id, parse_mode="HTML", reply_markup=users_pagination_keyboard(page, data['total_pages']))
            except Exception: pass

        elif action == "find":
            _admin_state[call.from_user.id] = "find"
            try: bot.edit_message_text("🔍 Введите <b>ID</b> или <b>@username</b>:", chat_id, msg_id, parse_mode="HTML", reply_markup=cancel_button())
            except Exception: pass

        elif action.startswith("msg:"):
            target_id = int(action.split(":")[1])
            _admin_state[call.from_user.id] = {"action": "send_msg", "target_id": target_id}
            try: bot.edit_message_text(f"✉️ Введите текст для <code>{target_id}</code>:", chat_id, msg_id, parse_mode="HTML", reply_markup=cancel_button())
            except Exception: pass

        elif action == "broadcast":
            _admin_state[call.from_user.id] = {"step": "text"}
            try: bot.edit_message_text("📢 <b>Шаг 1/3.</b> Отправьте текст рассылки.", chat_id, msg_id, parse_mode="HTML", reply_markup=cancel_button())
            except Exception: pass

        elif action == "broadcast_skip_photo":
            data = _admin_state.get(call.from_user.id)
            if not isinstance(data, dict) or not data.get("text"):
                return
            data["photo"] = None
            data["step"] = "confirm"
            _admin_state[call.from_user.id] = data
            try: bot.delete_message(chat_id, msg_id)
            except Exception: pass
            bot.send_message(chat_id, f"📢 <b>Шаг 3/3. Проверьте:</b>\n\n{data['text']}\n\nОтправляем?", parse_mode="HTML", reply_markup=confirm_broadcast_button())

        elif action == "broadcast_confirm":
            data = _admin_state.get(call.from_user.id)
            if not isinstance(data, dict): return
            _admin_state.pop(call.from_user.id, None)
            try: bot.edit_message_text("📢 Рассылка запущена...", chat_id, msg_id)
            except Exception: bot.send_message(chat_id, "📢 Рассылка запущена...")
            
            ids = get_all_user_ids(include_banned=False)
            ok, fail = 0, 0
            for uid in ids:
                try:
                    if data.get("photo"): bot.send_photo(uid, data["photo"], caption=data["text"], parse_mode="HTML")
                    else: bot.send_message(uid, data["text"], parse_mode="HTML")
                    ok += 1
                    time.sleep(0.05)
                except Exception: fail += 1
            bot.send_message(chat_id, f"✅ Доставлено: {ok}\nОшибок: {fail}")

        elif action.startswith("ban:"):
            uid = int(action.split(":")[1])
            if ban_user(uid):
                bot.answer_callback_query(call.id, "🚫 Забанен")
                try: bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=user_actions_keyboard(uid, banned=True))
                except Exception: pass

        elif action.startswith("unban:"):
            uid = int(action.split(":")[1])
            if unban_user(uid):
                bot.answer_callback_query(call.id, "✅ Разбанен")
                try: bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=user_actions_keyboard(uid, banned=False))
                except Exception: pass

        elif action.startswith("delete:"):
            uid = int(action.split(":")[1])
            try: bot.edit_message_text(f"🗑 Удалить <code>{uid}</code>?", chat_id, msg_id, parse_mode="HTML", reply_markup=confirm_delete_keyboard(uid))
            except Exception: pass

        elif action.startswith("delete_confirm:"):
            uid = int(action.split(":")[1])
            if delete_user(uid):
                try: bot.edit_message_text(f"✅ Пользователь <code>{uid}</code> удалён.", chat_id, msg_id, parse_mode="HTML", reply_markup=back_button())
                except Exception: pass

        bot.answer_callback_query(call.id)


    @bot.message_handler(
        func=lambda m: _admin_state.get(m.from_user.id) is not None and is_admin(m.from_user.id),
        content_types=["text", "photo"],
    )
    def handle_admin_text(message: types.Message):
        state = _admin_state.get(message.from_user.id)
        if not isinstance(state, dict) and state not in ("find",):
            return

        if state == "find":
            _admin_state.pop(message.from_user.id, None)
            text = (message.text or "").strip()
            if not text: return
            user = find_user(text)
            if not user:
                bot.send_message(message.chat.id, "❌ Не найден.")
                return
            b_stat = "🚫 Забанен" if user["is_banned"] else "✅ Активен"
            info = (
                f"🔍 <b>Найден:</b>\n\nID: <code>{user['telegram_id']}</code>\nИмя: {user['first_name'] or '—'}\n"
                f"Username: @{user['username'] or '—'}\nКод: <code>{user['referral_code']}</code>\n"
                f"Пригласил: <b>{user['referrals_count']}</b>\nСтатус: {b_stat}"
            )
            bot.send_message(message.chat.id, info, parse_mode="HTML", reply_markup=user_actions_keyboard(user["telegram_id"], banned=user["is_banned"]))
            return

        if state.get("action") == "send_msg":
            target_id = state["target_id"]
            _admin_state.pop(message.from_user.id, None)
            if not message.text:
                bot.send_message(message.chat.id, "⚠️ Отправьте текст.")
                return
            try:
                bot.send_message(target_id, f"💬 <b>Сообщение от администрации:</b>\n\n{message.text}", parse_mode="HTML")
                bot.send_message(message.chat.id, f"✅ Отправлено пользователю <code>{target_id}</code>.", parse_mode="HTML")
            except Exception:
                bot.send_message(message.chat.id, "❌ Ошибка (возможно, заблокировал).")
            return

        if state.get("step") == "text":
            if not message.text: return
            state["text"] = message.text
            state["step"] = "photo"
            _admin_state[message.from_user.id] = state
            bot.send_message(message.chat.id, "📢 <b>Шаг 2/3.</b> Отправьте фото или нажмите кнопку.", parse_mode="HTML", reply_markup=skip_photo_keyboard())
            return

        if state.get("step") == "photo":
            state["photo"] = message.photo[-1].file_id if message.photo else None
            state["step"] = "confirm"
            _admin_state[message.from_user.id] = state
            preview = f"📢 <b>Шаг 3/3. Проверьте:</b>\n\n{state['text']}"
            if state.get("photo"):
                bot.send_photo(message.chat.id, state["photo"], caption=preview, parse_mode="HTML", reply_markup=confirm_broadcast_button())
            else:
                bot.send_message(message.chat.id, preview, parse_mode="HTML", reply_markup=confirm_broadcast_button())
            return
