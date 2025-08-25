import json
import os
from flask import Blueprint, request, jsonify, session
from cryptography.fernet import Fernet

register_bp = Blueprint("register_bp", __name__)

# Caminho da chave
KEY_FILE = "data/fernet.key"

# Função para carregar ou gerar a chave
def load_or_create_key():
    if not os.path.exists(KEY_FILE):
        # Gera nova chave
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        print("Chave Fernet criada com sucesso!")
    else:
        with open(KEY_FILE, "rb") as f:
            key = f.read()
    return key

# Carrega ou cria a chave
key = load_or_create_key()
cipher = Fernet(key)

USERS_FILE = "data/users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        # cria arquivo vazio
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            f.write("[]")
        return []
    
    # arquivo existe, tenta carregar
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            # caso o arquivo esteja vazio ou inválido, reinicia
            with open(USERS_FILE, "w", encoding="utf-8") as fw:
                fw.write("[]")
            return []

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)

@register_bp.route("/login", methods=["POST"])
def login_user():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"status": "error", "message": "Email e senha são obrigatórios."}), 400

    users = load_users()
    for u in users:
        decrypted_email = cipher.decrypt(u["email"].encode()).decode()
        decrypted_password = cipher.decrypt(u["password"].encode()).decode()
        if decrypted_email.lower() == email.lower():
            if decrypted_password == password:
                session["user_logged_in"] = True
                session["username"] = u["username"]
                return jsonify({"status": "success", "message": f"Bem-vindo de volta, {u['username']}!"})
            else:
                return jsonify({"status": "fail", "message": "Senha incorreta."}), 400

    # se chegar aqui, email não encontrado
    return jsonify({"status": "fail", "reason": "not_found", "message": "Usuário não cadastrado."}), 400


@register_bp.route("/register", methods=["POST"])
def register_user():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"status": "error", "message": "Todos os campos são obrigatórios."}), 400

    # Criptografar email e senha
    encrypted_email = cipher.encrypt(email.encode()).decode()
    encrypted_password = cipher.encrypt(password.encode()).decode()

    users = load_users()

    # Verifica se username ou email já existem
    for u in users:
        # Descriptografa email existente para comparar
        decrypted_email = cipher.decrypt(u["email"].encode()).decode()
        if u["username"].lower() == username.lower():
            return jsonify({"status": "error", "message": "Usuário já existe."}), 400
        if decrypted_email.lower() == email.lower():
            return jsonify({"status": "error", "message": "Email já cadastrado."}), 400

    # Adiciona novo usuário
    users.append({
        "username": username,
        "email": encrypted_email,
        "password": encrypted_password
    })

    save_users(users)

    # ==================== LOGIN AUTOMÁTICO ====================
    session["user_logged_in"] = True
    session["username"] = username

    return jsonify({"status": "success", "message": "Cadastro realizado com sucesso!"})