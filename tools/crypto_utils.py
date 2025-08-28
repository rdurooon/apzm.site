import os
from cryptography.fernet import Fernet

KEY_FILE = os.path.join("data", "fernet.key")

def load_or_create_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        print("✅ Nova chave Fernet criada em", KEY_FILE)
    else:
        with open(KEY_FILE, "rb") as f:
            key = f.read()
    return key

# 🔑 Inicializa cipher global
key = load_or_create_key()
cipher = Fernet(key)

def encrypt_value(value: str) -> str:
    return cipher.encrypt(value.encode()).decode()

def decrypt_value(value: str) -> str:
    try:
        return cipher.decrypt(value.encode()).decode()
    except Exception:
        return None
