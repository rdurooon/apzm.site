from cryptography.fernet import Fernet
key = Fernet.generate_key()
cipher = Fernet(key)
with open("data/fernet.key", "wb") as f:
    f.write(key)
