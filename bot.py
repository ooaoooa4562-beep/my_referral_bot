import os
import base64
import threading
import telebot
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests

from config import BOT_TOKEN
from database import (
    init_db, is_banned, spend_token, get_tokens, get_user
)
from handlers import start, my_ref, help, admin, menu_buttons

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

    # --- ТОЛЬКО CLOUDFLARE (Модель Lightning) ---
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
            # Если ошибка от Cloudflare, показываем её
            error_text = response.text[:150] if response.text else "Empty"
            return jsonify({"success": False, "error": f"Ошибка Cloudflare: {response.status_code}"})
            
    except Exception as e:
        return jsonify({"success": False, "error": "Сервер не ответил вовремя. Попробуйте позже."})

@app.route("/health")
def health():
    return "Bot is running", 200

def run_bot():
    init_db()
    print("Бот запущен...")
    bot.infinity_polling()

def main():
    start.register(bot)
    my_ref.register(bot)
    help.register(bot)
    admin.register(bot)
    menu_buttons.register(bot)

    @bot.message_handler(func=lambda m: is_banned(m.from_user.id), content_types=["text"])
    def block_banned(message): return

    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    main()
