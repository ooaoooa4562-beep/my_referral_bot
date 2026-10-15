import sqlite3
import secrets

from config import DB_PATH
from .models import CREATE_USERS_TABLE


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # доступ к колонкам по имени
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(CREATE_USERS_TABLE)
    conn.commit()
    conn.close()


def get_user(telegram_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(telegram_id: int, username: str, first_name: str) -> str:
    """Создаёт пользователя, если его нет. Возвращает его реферальный код."""
    conn = get_conn()
    cur = conn.cursor()

    # Если уже есть — обновляем username/first_name
    cur.execute("SELECT referral_code FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cur.fetchone()
    if row:
        cur.execute(
            "UPDATE users SET username = ?, first_name = ? WHERE telegram_id = ?",
            (username, first_name, telegram_id),
        )
        conn.commit()
        code = row["referral_code"]
        conn.close()
        return code

    # Создаём нового
    code = secrets.token_urlsafe(6)
    cur.execute(
        """
        INSERT INTO users (telegram_id, username, first_name, referral_code)
        VALUES (?, ?, ?, ?)
        """,
        (telegram_id, username, first_name, code),
    )
    conn.commit()
    conn.close()
    return code


def get_user_by_code(code: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT telegram_id FROM users WHERE referral_code = ?", (code,))
    row = cur.fetchone()
    conn.close()
    return row["telegram_id"] if row else None


def set_referrer(new_user_id: int, referrer_id: int) -> bool:
    if new_user_id == referrer_id:
        return False

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT referred_by FROM users WHERE telegram_id = ?", (new_user_id,))
    row = cur.fetchone()
    if not row or row["referred_by"] is not None:
        conn.close()
        return False

    cur.execute(
        "UPDATE users SET referred_by = ? WHERE telegram_id = ?",
        (referrer_id, new_user_id),
    )
    cur.execute(
        "UPDATE users SET referrals_count = referrals_count + 1 WHERE telegram_id = ?",
        (referrer_id,),
    )
    conn.commit()
    conn.close()
    return True


def get_referrals_count(user_id: int) -> int:
    user = get_user(user_id)
    return user["referrals_count"] if user else 0
