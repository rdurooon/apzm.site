import json
import os
from tools.crypto_utils import encrypt_value, decrypt_value

USERS_FILE = os.path.join("data", "users.json")

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def update_user_password(email: str, new_password: str) -> bool:
    users = load_users()
    for user in users:
        try:
            decrypted_email = decrypt_value(user["email"])
        except Exception:
            continue

        if decrypted_email == email:
            user["password"] = encrypt_value(new_password)
            save_users(users)
            return True
    return False

# /tools/users_manip.py
def user_exists(email: str) -> bool:
    """Verifica se o email existe no banco de usuários (descriptografando)."""
    users = load_users()
    for user in users:
        try:
            decrypted_email = decrypt_value(user["email"])
        except Exception:
            continue
        if decrypted_email == email:
            return True
    return False

