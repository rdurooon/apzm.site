import os
import secrets
import tempfile

SECRET_KEY_FILE = os.path.join("data", "secret_key.key")


def get_or_create_secret_key() -> str:
    os.makedirs(os.path.dirname(SECRET_KEY_FILE), exist_ok=True)

    if os.path.exists(SECRET_KEY_FILE):
        with open(SECRET_KEY_FILE, "r", encoding="utf-8") as handle:
            return handle.read().strip()

    key = secrets.token_hex(64)
    temp_fd, temp_path = tempfile.mkstemp(prefix="secret_key_", dir=os.path.dirname(SECRET_KEY_FILE))
    try:
        os.fchmod(temp_fd, 0o600)
        with os.fdopen(temp_fd, "w", encoding="utf-8") as handle:
            handle.write(key)
        os.replace(temp_path, SECRET_KEY_FILE)
        os.chmod(SECRET_KEY_FILE, 0o600)
    except Exception:
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
        raise

    return key
