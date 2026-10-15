import secrets
import psycopg2
from psycopg2.extras import RealDictCursor

from config import DATABASE_URL

# Render отдаёт URL в формате postgres://, а psycopg2 требует postgresql://
_db_url = DATABASE_URL
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)


def get_conn():
    return psycopg2.connect(_db_url, cursor_factory=RealDictCursor)


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
            created_at      TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def get_user(telegram_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def create_user(telegram_id: int, username: str, first_name: str) -> str:
    """Создаёт пользователя, если его нет. Возвращает его реферальный код."""
    conn = get_conn()
    cur = conn.cursor()

    # Если пользователь уже есть — обновляем username/first_name и возвращаем код
    cur.execute("SELECT referral_code FROM users WHERE telegram_id = %s", (telegram_id,))
    row = cur.fetchone()
    if row:
        cur.execute(
            "UPDATE users SET username = %s, first_name = %s WHERE telegram_id = %s",
            (username, first_name, telegram_id),
        )
        conn.commit()
        cur.close()
        conn.close()
        return row["referral_code"]

    # Создаём нового
    code = secrets.token_urlsafe(6)
    cur.execute("""
        INSERT INTO users (telegram_id, username, first_name, referral_code)
        VALUES (%s, %s, %s, %s)
    """, (telegram_id, username, first_name, code))
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
    """Привязывает нового пользователя к пригласившему."""
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

    cur.execute(
        "UPDATE users SET referred_by = %s WHERE telegram_id = %s",
        (referrer_id, new_user_id),
    )
    cur.execute(
        "UPDATE users SET referrals_count = referrals_count + 1 WHERE telegram_id = %s",
        (referrer_id,),
    )
    conn.commit()
    cur.close()
    conn.close()
    return True


def get_referrals_count(user_id: int) -> int:
    user = get_user(user_id)
    return user["referrals_count"] if user else 0
