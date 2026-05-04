import hashlib
import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from flask import g
from werkzeug.security import check_password_hash, generate_password_hash
import pytz
from tools.crypto_utils import encrypt_value, decrypt_value

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATABASE_PATH = os.path.join(DATA_DIR, "apzm_database.db")

SQL_INIT = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email_encrypted TEXT NOT NULL,
    email_hash TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0,
    is_over_18 INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    username_change_locked_until DATETIME DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS cards (
    file TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    visible INTEGER NOT NULL DEFAULT 1,
    is_new INTEGER NOT NULL DEFAULT 0,
    new_since DATETIME,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS card_links (
    card_file TEXT PRIMARY KEY,
    historia TEXT,
    mapa TEXT,
    FOREIGN KEY(card_file) REFERENCES cards(file) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS partners (
    file TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    descricao TEXT,
    site TEXT,
    instagram TEXT,
    twitter TEXT,
    discord TEXT,
    email TEXT
);

CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    subtitle TEXT,
    text TEXT NOT NULL,
    image TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    button_text TEXT,
    button_type TEXT,
    button_target TEXT,
    button_url TEXT
);

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id TEXT NOT NULL,
    username TEXT NOT NULL,
    comment TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY(card_id) REFERENCES cards(file) ON DELETE CASCADE,
    UNIQUE(card_id, username)
);

CREATE TABLE IF NOT EXISTS likes (
    card_file TEXT NOT NULL,
    username TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY(card_file, username),
    FOREIGN KEY(card_file) REFERENCES cards(file) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ratings (
    item_id TEXT NOT NULL,
    username TEXT NOT NULL,
    rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
    created_at DATETIME NOT NULL,
    PRIMARY KEY(item_id, username)
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def get_db():
    if "db" not in g:
        connection = sqlite3.connect(DATABASE_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.db = connection
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
    init_db()


def hash_value(value: str) -> str:
    normalized = (value or "").strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def dict_from_row(row):
    return dict(row) if row is not None else None


def now_str() -> str:
    return datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat()


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    db = sqlite3.connect(DATABASE_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(SQL_INIT)
    _ensure_users_table_columns(db)
    db.commit()
    _seed_data(db)
    db.close()


def _table_is_empty(db, table_name):
    cursor = db.execute(f"SELECT 1 FROM {table_name} LIMIT 1")
    return cursor.fetchone() is None


def _column_exists(db, table_name, column_name):
    cursor = db.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def _ensure_users_table_columns(db):
    if not _column_exists(db, "users", "username_change_locked_until"):
        db.execute(
            "ALTER TABLE users ADD COLUMN username_change_locked_until DATETIME DEFAULT NULL"
        )


def _seed_data(db):
    if _table_is_empty(db, "settings"):
        db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                   ("site_online", "1"))
    db.commit()


def get_user_by_username(username):
    db = get_db()
    row = db.execute(
        "SELECT * FROM users WHERE LOWER(username) = LOWER(?)",
        (username or "",)
    ).fetchone()
    return dict_from_row(row)


def get_user_by_email(email):
    db = get_db()
    row = db.execute(
        "SELECT * FROM users WHERE email_hash = ?",
        (hash_value(email),)
    ).fetchone()
    return dict_from_row(row)


def create_user(username, email, password, is_admin=False):
    db = get_db()
    now = now_str()
    user_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO users (id, username, email_encrypted, email_hash, password_hash, is_admin, is_over_18, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            user_id,
            username.strip(),
            encrypt_value(email.strip()),
            hash_value(email),
            generate_password_hash(password),
            1 if is_admin else 0,
            0,
            now,
        )
    )
    db.commit()
    return user_id


def update_user_password(email, new_password):
    db = get_db()
    result = db.execute(
        "UPDATE users SET password_hash = ? WHERE email_hash = ?",
        (generate_password_hash(new_password), hash_value(email))
    )
    db.commit()
    return result.rowcount > 0


def user_exists(email):
    return get_user_by_email(email) is not None


def get_all_users():
    db = get_db()
    rows = db.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    return [dict_from_row(row) for row in rows]


def get_admin_count():
    db = get_db()
    row = db.execute("SELECT COUNT(*) AS count FROM users WHERE is_admin = 1").fetchone()
    return row["count"] if row else 0


def promote_user(user_id):
    db = get_db()
    result = db.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
    db.commit()
    return result.rowcount > 0


def demote_user(user_id):
    db = get_db()
    result = db.execute("UPDATE users SET is_admin = 0 WHERE id = ?", (user_id,))
    db.commit()
    return result.rowcount > 0


def delete_user(user_id):
    db = get_db()
    result = db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    return result.rowcount > 0


def delete_user_by_username(username):
    db = get_db()
    result = db.execute("DELETE FROM users WHERE LOWER(username) = LOWER(?)", (username or "",))
    db.commit()
    return result.rowcount > 0


def set_user_over18(username, is_over18):
    db = get_db()
    result = db.execute(
        "UPDATE users SET is_over_18 = ? WHERE LOWER(username) = LOWER(?)",
        (1 if is_over18 else 0, username or "")
    )
    db.commit()
    return result.rowcount > 0


def can_change_username(username):
    """Verifica se o usuário pode alterar seu username."""
    db = get_db()
    user = db.execute(
        "SELECT username_change_locked_until FROM users WHERE LOWER(username) = LOWER(?)",
        (username or "",)
    ).fetchone()
    
    if not user or not user["username_change_locked_until"]:
        return True, None
    
    lock_until = datetime.fromisoformat(user["username_change_locked_until"])
    now = datetime.now(pytz.timezone("America/Sao_Paulo"))
    
    if now >= lock_until:
        return True, None
    
    return False, lock_until


def update_username(old_username, new_username):
    """Atualiza o username e aplica o lock de 14 dias."""
    db = get_db()
    
    # Verifica se o novo username já existe em outro usuário
    existing = db.execute(
        "SELECT id FROM users WHERE LOWER(username) = LOWER(?) AND LOWER(username) != LOWER(?)",
        (new_username or "", old_username or "")
    ).fetchone()
    
    if existing:
        return False, "Usuário já existe."
    
    # Calcula a data de desbloqueio (14 dias depois)
    tz = pytz.timezone("America/Sao_Paulo")
    now = datetime.now(tz)
    unlock_date = now + timedelta(days=14)
    
    result = db.execute(
        "UPDATE users SET username = ?, username_change_locked_until = ? WHERE LOWER(username) = LOWER(?)",
        (new_username.strip(), unlock_date.isoformat(), old_username or "")
    )
    db.commit()
    
    if result.rowcount > 0:
        return True, "Username alterado com sucesso!"
    
    return False, "Falha ao alterar username."


def get_site_status():
    db = get_db()
    row = db.execute("SELECT value FROM settings WHERE key = ?", ("site_online",)).fetchone()
    if not row:
        return True
    return row["value"] == "1"


def set_site_status(is_online):
    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        ("site_online", "1" if is_online else "0")
    )
    db.commit()
    return True


def get_visible_cards():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM cards WHERE visible = 1 ORDER BY sort_order ASC"
    ).fetchall()
    return [dict_from_row(row) for row in rows]


def get_cards():
    db = get_db()
    rows = db.execute("SELECT * FROM cards ORDER BY sort_order ASC").fetchall()
    return [dict_from_row(row) for row in rows]


def get_card_by_file(file_name):
    db = get_db()
    row = db.execute("SELECT * FROM cards WHERE file = ?", (file_name,)).fetchone()
    return dict_from_row(row)


def insert_card(file_name, title, description):
    db = get_db()
    current_max = db.execute("SELECT COALESCE(MAX(sort_order), -1) FROM cards").fetchone()[0]
    db.execute(
        "INSERT INTO cards (file, title, description, visible, is_new, new_since, sort_order) VALUES (?, ?, ?, 1, 0, NULL, ?)",
        (file_name, title, description or "", current_max + 1)
    )
    db.commit()
    return True


def delete_card(file_name):
    db = get_db()
    result = db.execute("DELETE FROM cards WHERE file = ?", (file_name,))
    db.commit()
    return result.rowcount > 0


def update_card(file_name, title=None, description=None, visible=None, is_new=None, new_since=None, sort_order=None):
    db = get_db()
    updates = []
    params = []
    if title is not None:
        updates.append("title = ?")
        params.append(title)
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    if visible is not None:
        updates.append("visible = ?")
        params.append(1 if visible else 0)
    if is_new is not None:
        updates.append("is_new = ?")
        params.append(1 if is_new else 0)
    if new_since is not None:
        updates.append("new_since = ?")
        params.append(new_since)
    if sort_order is not None:
        updates.append("sort_order = ?")
        params.append(sort_order)
    if not updates:
        return False
    params.append(file_name)
    db.execute(f"UPDATE cards SET {', '.join(updates)} WHERE file = ?", tuple(params))
    db.commit()
    return True


def update_cards_order(cards_data):
    db = get_db()
    for index, card in enumerate(cards_data):
        file_name = card.get("file")
        if not file_name:
            continue
        db.execute(
            "UPDATE cards SET visible = ?, sort_order = ?, title = ?, description = ? WHERE file = ?",
            (
                1 if card.get("visible", True) else 0,
                index,
                card.get("title") or os.path.splitext(file_name)[0].capitalize(),
                card.get("description") or "",
                file_name,
            )
        )
    db.commit()
    return True


def get_card_links():
    db = get_db()
    rows = db.execute("SELECT * FROM card_links").fetchall()
    return {row["card_file"]: {"historia": row["historia"], "mapa": row["mapa"]} for row in rows}


def save_card_links(file_name, historia, mapa):
    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO card_links (card_file, historia, mapa) VALUES (?, ?, ?)",
        (file_name, historia or "", mapa or "")
    )
    db.commit()
    return True


def get_partners():
    db = get_db()
    rows = db.execute("SELECT * FROM partners ORDER BY nome ASC").fetchall()
    return [dict_from_row(row) for row in rows]


def _build_news_item(row):
    if row is None:
        return None
    item = dict_from_row(row)
    if item is None:
        return None

    button = None
    if item.get("button_text") or item.get("button_type") or item.get("button_target") or item.get("button_url"):
        button = {
            "text": item.get("button_text") or "",
            "type": item.get("button_type") or "",
            "target": item.get("button_target") or "",
            "url": item.get("button_url") or "",
        }
    item.pop("button_text", None)
    item.pop("button_type", None)
    item.pop("button_target", None)
    item.pop("button_url", None)
    item["button"] = button
    return item


def list_news():
    db = get_db()
    rows = db.execute("SELECT * FROM news ORDER BY id DESC").fetchall()
    return [_build_news_item(row) for row in rows]


def get_news_item(news_id):
    db = get_db()
    row = db.execute("SELECT * FROM news WHERE id = ?", (news_id,)).fetchone()
    return _build_news_item(row)


def insert_news(title, subtitle, text, image, button):
    db = get_db()
    created_at = datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat()
    button_text = button.get("text") if button else None
    button_type = button.get("type") if button else None
    button_target = button.get("target") if button else None
    button_url = button.get("url") if button else None
    cursor = db.execute(
        "INSERT INTO news (title, subtitle, text, image, created_at, button_text, button_type, button_target, button_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (title, subtitle or "", text or "", image or "", created_at, button_text, button_type, button_target, button_url)
    )
    db.commit()
    return cursor.lastrowid


def update_news(news_id, title, subtitle, text, image, button):
    db = get_db()
    button_text = button.get("text") if button else None
    button_type = button.get("type") if button else None
    button_target = button.get("target") if button else None
    button_url = button.get("url") if button else None
    result = db.execute(
        "UPDATE news SET title = ?, subtitle = ?, text = ?, image = ?, button_text = ?, button_type = ?, button_target = ?, button_url = ? WHERE id = ?",
        (title, subtitle or "", text or "", image or "", button_text, button_type, button_target, button_url, news_id)
    )
    db.commit()
    return result.rowcount > 0


def delete_news(news_id):
    db = get_db()
    result = db.execute("DELETE FROM news WHERE id = ?", (news_id,))
    db.commit()
    return result.rowcount > 0


def get_comments_for_card(card_id):
    db = get_db()
    rows = db.execute("SELECT username, comment FROM comments WHERE card_id = ?", (card_id,)).fetchall()
    return {row["username"]: row["comment"] for row in rows}


def add_or_update_comment(card_id, username, comment_text):
    db = get_db()
    now = datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat()
    db.execute(
        "INSERT INTO comments (card_id, username, comment, created_at) VALUES (?, ?, ?, ?) ON CONFLICT(card_id, username) DO UPDATE SET comment = excluded.comment, created_at = excluded.created_at",
        (card_id, username, comment_text, now)
    )
    db.commit()
    return True


def delete_comment(card_id, username):
    db = get_db()
    result = db.execute("DELETE FROM comments WHERE card_id = ? AND username = ?", (card_id, username))
    db.commit()
    return result.rowcount > 0


def get_likes_for_card(filename, username=None):
    db = get_db()
    likes_count = db.execute("SELECT COUNT(*) AS count FROM likes WHERE card_file = ?", (filename,)).fetchone()["count"]
    liked = False
    if username:
        liked = db.execute(
            "SELECT 1 FROM likes WHERE card_file = ? AND LOWER(username) = LOWER(?)",
            (filename, username)
        ).fetchone() is not None
    return likes_count, liked


def toggle_like_card(filename, username):
    db = get_db()
    existing = db.execute(
        "SELECT 1 FROM likes WHERE card_file = ? AND LOWER(username) = LOWER(?)",
        (filename, username)
    ).fetchone()
    if existing:
        db.execute("DELETE FROM likes WHERE card_file = ? AND LOWER(username) = LOWER(?)", (filename, username))
        action = "unliked"
    else:
        db.execute("INSERT INTO likes (card_file, username, created_at) VALUES (?, ?, ?)",
                   (filename, username, datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat()))
        action = "liked"
    db.commit()
    count = db.execute("SELECT COUNT(*) AS count FROM likes WHERE card_file = ?", (filename,)).fetchone()["count"]
    return action, count


def get_rating_for_item(item_id):
    db = get_db()
    rows = db.execute("SELECT username, rating FROM ratings WHERE item_id = ?", (item_id,)).fetchall()
    ratings = {row["username"]: row["rating"] for row in rows}
    average = 0
    if ratings:
        average = round(sum(ratings.values()) / len(ratings), 2)
    return {"usuarios": ratings, "media": average}


def set_rating(item_id, username, rating):
    db = get_db()
    db.execute(
        "INSERT INTO ratings (item_id, username, rating, created_at) VALUES (?, ?, ?, ?) ON CONFLICT(item_id, username) DO UPDATE SET rating = excluded.rating, created_at = excluded.created_at",
        (item_id, username, rating, datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat())
    )
    db.commit()
    return get_rating_for_item(item_id)


def check_new_badges(cards):
    updated = False
    now = datetime.now(pytz.timezone("America/Sao_Paulo"))
    for card in cards:
        if card.get("is_new") and card.get("new_since"):
            try:
                new_since = datetime.fromisoformat(card["new_since"])
                if now - new_since > timedelta(days=7):
                    update_card(card["file"], is_new=False, new_since=None)
                    card["is_new"] = False
                    card["new_since"] = None
                    updated = True
            except Exception:
                update_card(card["file"], is_new=False, new_since=None)
                card["new_since"] = None
                updated = True
    return cards
