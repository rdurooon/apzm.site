import json
import os
import uuid
from datetime import datetime
import pytz
from flask import Blueprint, request, jsonify, session
from tools.crypto_utils import cipher, encrypt_value, decrypt_value

register_bp = Blueprint("register_bp", __name__)

USERS_FILE = "data/users.json"


# ==========================
# Funções utilitárias
# ==========================
def load_users():
    """Carrega usuários do arquivo JSON, criando caso não exista ou esteja inválido."""
    if not os.path.exists(USERS_FILE):
        save_users([])
        return []

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        save_users([])
        return []


def save_users(users):
    """Salva a lista de usuários no JSON."""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)


def find_user_by_email(users, email):
    """Retorna usuário pelo email descriptografado, ou None."""
    for u in users:
        decrypted_email = decrypt_value(u.get("email", ""))
        if decrypted_email and decrypted_email.lower() == email.lower():
            return u
    return None


def find_user_by_username(users, username):
    """Retorna usuário pelo username (case insensitive), ou None."""
    for u in users:
        if u.get("username", "").lower() == username.lower():
            return u
    return None


def mask_password(password: str) -> str:
    """Retorna a senha mascarada (****)."""
    return "*" * len(password) if password else "********"


# ==========================
# Rotas de autenticação
# ==========================
@register_bp.route("/login", methods=["POST"])
def login_user():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"status": "error", "message": "Email e senha são obrigatórios."}), 400

    users = load_users()
    user = find_user_by_email(users, email)

    if not user:
        return jsonify({"status": "fail", "reason": "not_found", "message": "Usuário não cadastrado."}), 400

    if decrypt_value(user["password"]) != password:
        return jsonify({"status": "fail", "message": "Senha incorreta."}), 400

    # Sessão
    session.update({
        "user_logged_in": True,
        "username": user["username"],
        "is_admin": user.get("is_admin", False)
    })

    decrypted_email = decrypt_value(user.get("email", "")) or "não informado"
    raw_password = decrypt_value(user.get("password", "")) or ""

    return jsonify({
        "status": "success",
        "message": f"Bem-vindo de volta, {user['username']}!",
        "is_admin": user.get("is_admin", False),
        "email": decrypted_email,
        "password_masked": mask_password(raw_password),
    })


@register_bp.route("/register", methods=["POST"])
def register_user():
    data = request.get_json(silent=True) or {}
    username, email, password = data.get("username"), data.get("email"), data.get("password")

    if not username or not email or not password:
        return jsonify({"status": "error", "message": "Todos os campos são obrigatórios."}), 400

    users = load_users()

    if find_user_by_username(users, username):
        return jsonify({"status": "error", "message": "Usuário já existe."}), 400
    if find_user_by_email(users, email):
        return jsonify({"status": "error", "message": "Email já cadastrado."}), 400

    new_user = {
        "id": str(uuid.uuid4()),
        "username": username,
        "email": encrypt_value(email),
        "password": encrypt_value(password),
        "is_admin": False,
        "created_at": datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M:%S")
    }

    users.append(new_user)
    save_users(users)

    # Login automático
    session.update({
        "user_logged_in": True,
        "username": username,
        "is_admin": False
    })

    return jsonify({"status": "success", "message": "Cadastro realizado com sucesso!"})


# ==========================
# Funções administrativas
# ==========================
def promote_user(user_id):
    """Promove um usuário para admin."""
    users = load_users()
    for u in users:
        if u.get("id") == user_id and not u.get("is_admin", False):
            u["is_admin"] = True
            save_users(users)
            return True
    return False


def demote_user(user_id):
    """Remove status de admin de um usuário."""
    users = load_users()
    for u in users:
        if u.get("id") == user_id and u.get("is_admin", False):
            u["is_admin"] = False
            save_users(users)
            return True
    return False


def delete_user(user_id):
    """Deleta um usuário pelo ID."""
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

    data = request.get_json(silent=True) or {}
    username_to_delete = data.get("username")

    if not username_to_delete:
        return jsonify({"status": "error", "message": "Requisição inválida."}), 400
    if username_to_delete != session["username"]:
        return jsonify({"status": "error", "message": "Ação não permitida."}), 403

    users = load_users()
    for i, u in enumerate(users):
        if u.get("username") == username_to_delete:
            users.pop(i)
            save_users(users)
            session.clear()
            return jsonify({"status": "success", "message": "Conta deletada com sucesso!"})

    return jsonify({"status": "error", "message": "Usuário não encontrado."}), 404
