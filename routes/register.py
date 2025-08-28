import json
import os
import uuid
from flask import Blueprint, request, jsonify, session
from datetime import datetime
from tools.crypto_utils import cipher, encrypt_value, decrypt_value

register_bp = Blueprint("register_bp", __name__)

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
        decrypted_email = decrypt_value(u["email"])
        decrypted_password = decrypt_value(u["password"])
        if decrypted_email and decrypted_email.lower() == email.lower():
            if decrypted_password == password:
                session["user_logged_in"] = True
                session["username"] = u["username"]
                session["is_admin"] = u.get("is_admin", False)

                decrypted_email = decrypt_value(u.get("email", "")) or "não informado"
                raw_password = decrypt_value(u.get("password", "")) or ""
                password_masked = "*" * len(raw_password) if raw_password else "********"

                return jsonify({
                    "status": "success",
                    "message": f"Bem-vindo de volta, {u['username']}!",
                    "is_admin": u.get("is_admin", False),
                    "email": decrypted_email,
                    "password_masked": password_masked
                })
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
    # REGISTER
    encrypted_email = encrypt_value(email)
    encrypted_password = encrypt_value(password)

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
        "id": str(uuid.uuid4()),
        "username": username,
        "email": encrypted_email,
        "password": encrypted_password,
        "is_admin": False,
        "created_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    })

    save_users(users)

    # ==================== LOGIN AUTOMÁTICO ====================
    session["user_logged_in"] = True
    session["username"] = username
    session["is_admin"] = False

    return jsonify({"status": "success", "message": "Cadastro realizado com sucesso!"})

# ==========================
# Funções de manipulação de usuários (Admin)
# ==========================
def promote_user(user_id):
    """
    Promove um usuário para admin.
    Retorna True se sucesso, False se usuário não encontrado ou já for admin.
    """
    users = load_users()
    for u in users:
        if u.get("id") == user_id:
            if u.get("is_admin", False):
                return False  # já é admin
            u["is_admin"] = True
            save_users(users)
            return True
    return False

def demote_user(user_id):
    """
    Remove status de admin de um usuário.
    Retorna True se sucesso, False se usuário não encontrado ou não for admin.
    """
    users = load_users()
    for u in users:
        if u.get("id") == user_id:
            if not u.get("is_admin", False):
                return False  # não é admin
            u["is_admin"] = False
            save_users(users)
            return True
    return False

def delete_user(user_id):
    """
    Deleta um usuário.
    Retorna True se sucesso, False se usuário não encontrado.
    """
    users = load_users()
    for i, u in enumerate(users):
        if u.get("id") == user_id:
            users.pop(i)
            save_users(users)
            return True
    return False

@register_bp.route("/delete_account", methods=["POST"])
def api_delete_user():
    if not session.get("user_logged_in") or not session.get("username"):
        return jsonify({"status": "error", "message": "Usuário não logado."}), 401

    data = request.get_json()  # 🔹 garante leitura do JSON corretamente
    if not data or "username" not in data:
        return jsonify({"status": "error", "message": "Requisição inválida."}), 400

    username_to_delete = data.get("username")

    # Verifica se o username enviado bate com o da sessão
    if username_to_delete != session["username"]:
        return jsonify({"status": "error", "message": "Ação não permitida."}), 403

    users = load_users()
    user_found = False
    for i, u in enumerate(users):
        if u["username"] == username_to_delete:
            users.pop(i)
            user_found = True
            break

    if not user_found:
        return jsonify({"status": "error", "message": "Usuário não encontrado."}), 404

    # Salva alterações
    save_users(users)

    # Limpa sessão
    session.clear()

    return jsonify({"status": "success", "message": "Conta deletada com sucesso!"})