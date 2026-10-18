import os
import base64
import threading
import telebot
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import urllib.parse

from config import BOT_TOKEN
from database import (
    init_db, init_promocodes_table, is_banned, spend_token, get_tokens, get_user,
    redeem_promocode, get_invited_friends
)
from handlers import start, my_ref, help, admin, menu_buttons, dev_tools

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

    # --- ПОПЫТКА 1: Cloudflare ---
    try:
        url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/@cf/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": f"Bearer {CF_API_TOKEN}"}
        payload = {"prompt": prompt}

        # Делаем запрос к Cloudflare
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            image_base64 = base64.b64encode(response.content).decode("utf-8")
            image_url = f"data:image/png;base64,{image_base64}"
            return jsonify({"success": True, "image_url": image_url, "new_balance": get_tokens(user_id)})
        else:
            # Если Cloudflare вернул ошибку (например, 400 или 500), возвращаем текст ошибки
            error_text = response.text[:150] if response.text else "Empty"
            print(f"⚠️ Cloudflare Error {response.status_code}: {error_text}")
            return jsonify({"success": False, "error": f"Cloudflare Error {response.status_code}: {error_text}"})
            
    except Exception as e:
        print(f"⚠️ Cloudflare Exception: {e}")
        return jsonify({"success": False, "error": f"Cloudflare Timeout: {str(e)}"})

    # --- ПОПЫТКА 2: Pollinations (Резерв) ---
    # (Если Cloudflare упал, код сюда не дойдет, так как мы уже сделали return выше.
    #  Если вы хотите, чтобы при ошибке Cloudflare бот пробовал Pollinations, 
    #  удалите return в блоке else выше и раскомментируйте код ниже).
    
    # try:
    #     encoded_prompt = urllib.parse.quote(prompt)
    #     fallback_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=flux&nologo=true"
    #     fallback_resp = requests.get(fallback_url, timeout=120)
    #     if fallback_resp.status_code == 200:
    #         image_base64 = base64.b64encode(fallback_resp.content).decode("utf-8")
    #         image_url = f"data:image/png;base64,{image_base64}"
    #         return jsonify({"success": True, "image_url": image_url, "new_balance": get_tokens(user_id)})
    # except Exception as e:
    #     print(f"⚠️ Pollinations Exception: {e}")

@app.route("/api/promo", methods=["POST"])
def api_promo():
    data = request.json
    user_id = data.get("user_id")
    code = data.get("code")
    if not user_id or not code: return jsonify({"success": False, "error": "Нет данных"}), 400
    return jsonify(redeem_promocode(int(user_id), code))

@app.route("/api/friends", methods=["POST"])
def api_friends():
    data = request.json
    user_id = data.get("user_id")
    if not user_id: return jsonify({"error": "No user_id"}), 400
    return jsonify({"friends": get_invited_friends(int(user_id))})

@app.route("/health")
def health():
    return "Bot is running", 200

def run_bot():
    init_db()
    init_promocodes_table()
    print("Бот запущен...")
    bot.infinity_polling()

def main():
    start.register(bot)
    my_ref.register(bot)
    help.register(bot)
    admin.register(bot)
    menu_buttons.register(bot)
    dev_tools.register(bot)

    @bot.message_handler(func=lambda m: is_banned(m.from_user.id), content_types=["text"])
    def block_banned(message): return

    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    main()
