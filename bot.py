import os
import threading
import telebot
import requests
from urllib.parse import quote
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

from config import BOT_TOKEN
from database import init_db, is_banned, spend_token, get_tokens
from handlers import start, my_ref, help, admin, menu_buttons


app = Flask(__name__)
CORS(app)  # Разрешаем запросы от Mini App

bot = telebot.TeleBot(BOT_TOKEN)


# --- API ДЛЯ MINI APP ---
@app.route("/")
def index():
    # Отдаем HTML страницу
    return render_template("index.html")


@app.route("/api/balance", methods=["POST"])
def api_balance():
    data = request.json
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "No user_id"}), 400
    
    tokens = get_tokens(int(user_id))
    return jsonify({"tokens": tokens})


@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.json
    user_id = data.get("user_id")
    prompt = data.get("prompt")
    
    if not user_id or not prompt:
        return jsonify({"success": False, "error": "Нет данных"}), 400

    user_id = int(user_id)

    # 1. Пытаемся списать токен
    if not spend_token(user_id):
        return jsonify({"success": False, "error": "Недостаточно токенов"})

    # 2. Делаем запрос к Pollinations.ai
    try:
        # Переводим промпт в URL-формат
        encoded_prompt = quote(prompt)
        
        # ВАЖНО: Добавляем параметр model=zimage и просим убрать водяной знак
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=zimage&nologo=true"
        
        new_balance = get_tokens(user_id)
        
        return jsonify({
            "success": True, 
            "image_url": url,
            "new_balance": new_balance
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# --- БОТ ---
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

    @bot.message_handler(
        func=lambda m: is_banned(m.from_user.id),
        content_types=["text"],
    )
    def block_banned(message):
        return

    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
