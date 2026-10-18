import secrets
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

from config import DB_URL


def get_conn():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id     BIGINT PRIMARY KEY,
            username        TEXT,
            first_name      TEXT,
            referral_code   TEXT UNIQUE,
            referred_by     BIGINT,
            referrals_count INTEGER DEFAULT 0,
            is_banned       BOOLEAN DEFAULT FALSE,
            tokens          INTEGER DEFAULT 0,
            course_code     TEXT UNIQUE,
            created_at      TIMESTAMP DEFAULT NOW()
        )
    """)
    # Безопасно добавляем новые колонки
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT FALSE")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS tokens INTEGER DEFAULT 0")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS course_code TEXT UNIQUE")
    conn.commit()
    cur.close()
    conn.close()

    # Создаем таблицу промокодов
    init_promocodes_table()


def get_user(telegram_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def create_user(telegram_id: int, username: str, first_name: str) -> str:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT referral_code FROM users WHERE telegram_id = %s", (telegram_id,))
    row = cur.fetchone()
    if row:
        cur.execute(
            "UPDATE users SET username = %s, first_name = %s WHERE telegram_id = %s",
            (username, first_name, telegram_id),
        )
        conn.commit()
        code = row["referral_code"]
        cur.close()
        conn.close()
        return code

    code = secrets.token_urlsafe(6)
    cur.execute(
        "INSERT INTO users (telegram_id, username, first_name, referral_code) VALUES (%s, %s, %s, %s)",
        (telegram_id, username, first_name, code),
    )
    conn.commit()
    cur.close()
    conn.close()
    return code


def get_user_by_code(code: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT telegram_id FROM users WHERE referral_code = %s", (code,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row["telegram_id"] if row else None


def set_referrer(new_user_id: int, referrer_id: int) -> bool:
    if new_user_id == referrer_id:
        return False
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT referred_by FROM users WHERE telegram_id = %s", (new_user_id,))
    row = cur.fetchone()
    if not row or row["referred_by"] is not None:
        cur.close()
        conn.close()
        return False
    cur.execute("UPDATE users SET referred_by = %s WHERE telegram_id = %s", (referrer_id, new_user_id))
    cur.execute("UPDATE users SET referrals_count = referrals_count + 1 WHERE telegram_id = %s", (referrer_id,))
    conn.commit()
    cur.close()
    conn.close()
    return True


def get_referrals_count(user_id: int) -> int:
    user = get_user(user_id)
    return user["referrals_count"] if user else 0


def is_banned(telegram_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT is_banned FROM users WHERE telegram_id = %s", (telegram_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return bool(row and row["is_banned"])


def ban_user(telegram_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_banned = TRUE WHERE telegram_id = %s", (telegram_id,))
    changed = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    return changed


def unban_user(telegram_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_banned = FALSE WHERE telegram_id = %s", (telegram_id,))
    changed = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    return changed


def delete_user(telegram_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET referred_by = NULL WHERE referred_by = %s", (telegram_id,))
    cur.execute("DELETE FROM users WHERE telegram_id = %s", (telegram_id,))
    changed = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    return changed


def get_stats() -> dict:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM users")
    total = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM users WHERE referred_by IS NOT NULL")
    referred = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM users WHERE created_at > NOW() - INTERVAL '24 hours'")
    last_24h = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM users WHERE referrals_count > 0")
    referrers = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM users WHERE is_banned = TRUE")
    banned = cur.fetchone()["c"]
    cur.close()
    conn.close()
    return {"total": total, "referred": referred, "last_24h": last_24h, "referrers": referrers, "banned": banned}


def get_top_referrers(limit: int = 10) -> list:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT telegram_id, username, first_name, referrals_count FROM users WHERE referrals_count > 0 ORDER BY referrals_count DESC LIMIT %s",
        (limit,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_recent_users(limit: int = 20) -> list:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT telegram_id, username, first_name, referral_code, referrals_count, is_banned, created_at FROM users ORDER BY created_at DESC LIMIT %s",
        (limit,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def find_user(query: str):
    conn = get_conn()
    cur = conn.cursor()
    if query.isdigit():
        cur.execute("SELECT * FROM users WHERE telegram_id = %s", (int(query),))
    else:
        username = query.lstrip("@")
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def get_all_user_ids(include_banned: bool = False) -> list:
    conn = get_conn()
    cur = conn.cursor()
    if include_banned:
        cur.execute("SELECT telegram_id FROM users")
    else:
        cur.execute("SELECT telegram_id FROM users WHERE is_banned = FALSE")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r["telegram_id"] for r in rows]


def get_all_users_paginated(page: int, per_page: int = 10) -> dict:
    offset = (page - 1) * per_page
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM users")
    total = cur.fetchone()["c"]
    cur.execute(
        "SELECT telegram_id, username, first_name, is_banned, created_at FROM users ORDER BY created_at DESC LIMIT %s OFFSET %s",
        (per_page, offset)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    return {"users": rows, "total": total, "total_pages": total_pages, "page": page}


def get_invited_friends(telegram_id: int) -> list:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT first_name, username FROM users WHERE referred_by = %s", (telegram_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# --- ТОКЕНЫ ---
def add_tokens(telegram_id: int, amount: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET tokens = tokens + %s WHERE telegram_id = %s", (amount, telegram_id))
    conn.commit()
    cur.close()
    conn.close()


def spend_token(telegram_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT tokens FROM users WHERE telegram_id = %s", (telegram_id,))
    row = cur.fetchone()
    if row and row["tokens"] > 0:
        cur.execute("UPDATE users SET tokens = tokens - 1 WHERE telegram_id = %s", (telegram_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True
    cur.close()
    conn.close()
    return False


def get_tokens(telegram_id: int) -> int:
    user = get_user(telegram_id)
    return user["tokens"] if user else 0


# --- СИСТЕМА КУРСОВ ---
def set_course_code(telegram_id: int, code: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET course_code = %s WHERE telegram_id = %s", (code, telegram_id))
    conn.commit()
    cur.close()
    conn.close()


def get_user_by_course_code(code: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT telegram_id FROM users WHERE course_code = %s", (code,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row["telegram_id"] if row else None


# --- ПРОМОКОДЫ ---
def init_promocodes_table():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS promocodes (
            code TEXT PRIMARY KEY,
            reward INTEGER DEFAULT 1,
            usage_limit INTEGER DEFAULT 100,
            used_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def create_promocode(code: str, reward: int, limit: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO promocodes (code, reward, usage_limit) VALUES (%s, %s, %s) ON CONFLICT (code) DO NOTHING",
        (code.upper(), reward, limit)
    )
    conn.commit()
    cur.close()
    conn.close()


def redeem_promocode(telegram_id: int, code: str) -> dict:
    conn = get_conn()
    cur = conn.cursor()
    code = code.upper().strip()
    cur.execute("SELECT reward, usage_limit, used_count FROM promocodes WHERE code = %s", (code,))
    promo = cur.fetchone()
    if not promo:
        cur.close()
        conn.close()
        return {"success": False, "error": "Промокод не найден"}
    if promo["used_count"] >= promo["usage_limit"]:
        cur.close()
        conn.close()
        return {"success": False, "error": "Лимит использований исчерпан"}
    cur.execute("UPDATE promocodes SET used_count = used_count + 1 WHERE code = %s", (code,))
    cur.execute("UPDATE users SET tokens = tokens + %s WHERE telegram_id = %s", (promo["reward"], telegram_id))
    conn.commit()
    cur.execute("SELECT tokens FROM users WHERE telegram_id = %s", (telegram_id,))
    new_balance = cur.fetchone()["tokens"]
    cur.close()
    conn.close()
    return {"success": True, "reward": promo["reward"], "new_balance": new_balance}
