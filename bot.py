import os
import base64
import threading
import secrets
import telebot
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests

from config import BOT_TOKEN
from database import (
    init_db, is_banned, spend_token, get_tokens, get_user, add_tokens,
    set_course_code, get_user_by_course_code, create_user, get_referrals_count
)
from handlers import my_ref, help, admin, menu_buttons # Убрали start

app = Flask(__name__)
CORS(app)
bot = telebot.TeleBot(BOT_TOKEN)

CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID", "")
CF_API_TOKEN = os.getenv("CF_API_TOKEN", "")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/balance", methods=["POST"])
def api_balance():
    data = request.json
    user_id = data.get("user_id")
    if not user_id: return jsonify({"error": "No user_id"}), 400
    
    user_id = int(user_id)
    tokens = get_tokens(user_id)
    user = get_user(user_id)
    ref_link = ""
    if user:
        bot_username = bot.get_me().username
        ref_link = f"https://t.me/{bot_username}?start={user['referral_code']}"
    return jsonify({"tokens": tokens, "ref_link": ref_link})

@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.json
    user_id = data.get("user_id")
    prompt = data.get("prompt")
    if not user_id or not prompt: 
        return jsonify({"success": False, "error": "Нет данных"}), 400

    user_id = int(user_id)
    if not spend_token(user_id):
        return jsonify({"success": False, "error": "Недостаточно токенов"})

    try:
        url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/@cf/bytedance/stable-diffusion-xl-lightning"
        headers = {"Authorization": f"Bearer {CF_API_TOKEN}"}
        payload = {"prompt": prompt}

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            image_base64 = base64.b64encode(response.content).decode("utf-8")
            image_url = f"data:image/png;base64,{image_base64}"
            return jsonify({"success": True, "image_url": image_url, "new_balance": get_tokens(user_id)})
        else:
            return jsonify({"success": False, "error": f"Ошибка Cloudflare: {response.status_code}"})
            
    except Exception as e:
        return jsonify({"success": False, "error": "Сервер не ответил вовремя."})

@app.route("/health")
def health():
    return "Bot is running", 200

def run_bot():
    init_db()
    print("Бот запущен...")
    bot.infinity_polling()

def main():
    # Регистрируем остальные хэндлеры (start исключен)
    my_ref.register(bot)
    help.register(bot)
    admin.register(bot)
    menu_buttons.register(bot)

    # КАСТОМНЫЙ /START (с логикой курса)
    @bot.message_handler(commands=["start"])
    def custom_start(message: telebot.types.Message):
        if is_banned(message.from_user.id):
            return

        user_id = message.from_user.id
        username = message.from_user.username or ""
        first_name = message.from_user.first_name or ""
        
        referral_code = create_user(user_id, username, first_name)

        parts = (message.text or "").split(maxsplit=1)
        payload = parts[1] if len(parts) > 1 else None

        if payload and payload.startswith("course_"):
            course_code = payload.replace("course_", "")
            teacher_id = get_user_by_course_code(course_code)
            
            if teacher_id:
                try:
                    bot.send_message(
                        teacher_id,
                        f"🔥 <b>Новый ученик на курсе Python!</b>\n\n"
                        f"Имя: {first_name}\n"
                        f"Юзернейм: @{username or 'нет'}",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
                
                bot.send_message(
                    user_id, 
                    f"👋 Привет, {first_name}!\n\nТы успешно записался на курс Python. Жди инструкций!",
                    reply_markup=menu_buttons.main_reply_menu()
                )
                return

        bot_username = bot.get_me().username
        ref_link = f"https://t.me/{bot_username}?start={referral_code}"
        count = get_referrals_count(user_id)
        tokens = get_tokens(user_id)
        
        text = (
            f"👋 Привет, <b>{first_name}</b>!\n\n"
            f"🪙 Твои токены: <b>{tokens}</b>\n\n"
            f"Твоя ссылка для друзей:\n<code>{ref_link}</code>"
        )
        bot.send_message(user_id, text, parse_mode="HTML", reply_markup=menu_buttons.main_reply_menu())

    # ССЫЛКА НА КУРС ДЛЯ УЧИТЕЛЯ
    @bot.message_handler(commands=["my_course"])
    def cmd_my_course(message: telebot.types.Message):
        if is_banned(message.from_user.id): return
            
        user = get_user(message.from_user.id)
        if not user:
            bot.reply_to(message, "Сначала напишите /start")
            return

        course_code = user.get("course_code")
        if not course_code:
            course_code = secrets.token_urlsafe(6)
            set_course_code(message.from_user.id, course_code)

        bot_username = bot.get_me().username
        course_link = f"https://t.me/{bot_username}?start=course_{course_code}"

        bot.send_message(
            message.chat.id,
            f"🎓 <b>Твоя ссылка на курс Python:</b>\n\n"
            f"<code>{course_link}</code>\n\n"
            f"Отправь её ученикам. Когда они нажмут Start, тебе придет уведомление!",
            parse_mode="HTML"
        )

    # КОМАНДА /give ДЛЯ РАЗРАБОТЧИКОВ
    @bot.message_handler(commands=["give"])
    def cmd_give(message: telebot.types.Message):
        if message.from_user.id not in [5095658068, 8261666607]:
            return

        args = message.text.split()
        if len(args) < 2 or not args[1].isdigit():
            bot.reply_to(message, "⚠️ Формат: <code>/give 100</code>", parse_mode="HTML")
            return

        amount = int(args[1])
        add_tokens(message.from_user.id, amount)
        new_balance = get_tokens(message.from_user.id)
        
        bot.reply_to(message, f"✅ Начислено <b>{amount}</b> токенов!\nБаланс: <b>{new_balance}</b>", parse_mode="HTML")

    @bot.message_handler(func=lambda m: is_banned(m.from_user.id), content_types=["text"])
    def block_banned(message): return

    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    main()
