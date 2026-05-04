import uuid
from datetime import datetime
import pytz
from flask import Blueprint, request, jsonify, session
from werkzeug.security import check_password_hash
from tools.crypto_utils import encrypt_value, decrypt_value
from tools.db import (
    create_user,
    get_user_by_email,
    get_user_by_username,
    promote_user as db_promote_user,
    demote_user as db_demote_user,
    delete_user as db_delete_user,
    delete_user_by_username,
    set_user_over18 as db_set_user_over18,
    can_change_username,
    update_username,
)

register_bp = Blueprint("register_bp", __name__)


def mask_password(password: str) -> str:
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

    user = get_user_by_email(email)
    if not user:
        return jsonify({"status": "fail", "reason": "not_found", "message": "Usuário não cadastrado."}), 400

    if not check_password_hash(user["password_hash"], password):
        return jsonify({"status": "fail", "message": "Senha incorreta."}), 400

    session.update({
        "user_logged_in": True,
        "username": user["username"],
        "is_admin": bool(user.get("is_admin", False))
    })

    decrypted_email = decrypt_value(user.get("email_encrypted", "")) or "não informado"
    return jsonify({
        "status": "success",
        "message": f"Bem-vindo de volta, {user['username']}!",
        "username": user["username"],
        "is_over_18": bool(user.get("is_over_18", False)),
        "is_admin": bool(user.get("is_admin", False)),
        "email": decrypted_email,
        "password_masked": mask_password(password),
    })


@register_bp.route("/register", methods=["POST"])
def register_user():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"status": "error", "message": "Todos os campos são obrigatórios."}), 400

    if get_user_by_username(username):
        return jsonify({"status": "error", "message": "Usuário já existe."}), 400
    if get_user_by_email(email):
        return jsonify({"status": "error", "message": "Email já cadastrado."}), 400

    create_user(username, email, password, is_admin=False)

    session.update({
        "user_logged_in": True,
        "username": username,
        "is_admin": False
    })

    return jsonify({
        "status": "success",
        "message": "Cadastro realizado com sucesso!",
        "username": username,
        "is_over_18": False,
        "is_admin": False,
    })


# ==========================
# Funções administrativas
# ==========================

def promote_user(user_id):
    return db_promote_user(user_id)


def demote_user(user_id):
    return db_demote_user(user_id)


def delete_user(user_id):
    return db_delete_user(user_id)


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

    if delete_user_by_username(username_to_delete):
        session.clear()
        return jsonify({"status": "success", "message": "Conta deletada com sucesso!"})

    return jsonify({"status": "error", "message": "Usuário não encontrado."}), 404


# ==========================
# Rotas para alterar dados da conta
# ==========================

@register_bp.route("/api/check_username_lock", methods=["POST"])
def check_username_lock():
    """Verifica se o usuário pode alterar seu username."""
    if not session.get("user_logged_in") or not session.get("username"):
        return jsonify({"status": "error", "message": "Usuário não logado."}), 401

    username = session["username"]
    can_change, lock_until = can_change_username(username)
    
    response = {
        "status": "success",
        "can_change": can_change,
        "locked_until": lock_until.isoformat() if lock_until else None
    }
    
    return jsonify(response)


@register_bp.route("/api/change_username", methods=["POST"])
def change_username():
    """Altera o username do usuário após validar a senha."""
    if not session.get("user_logged_in") or not session.get("username"):
        return jsonify({"status": "error", "message": "Usuário não logado."}), 401

    data = request.get_json(silent=True) or {}
    new_username = data.get("new_username", "").strip()
    password = data.get("password", "")
    
    if not new_username or not password:
        return jsonify({"status": "error", "message": "Novo username e senha são obrigatórios."}), 400
    
    current_username = session["username"]
    
    # Verifica se o usuário pode alterar o username
    can_change, lock_until = can_change_username(current_username)
    if not can_change:
        days_remaining = (lock_until - datetime.now(pytz.timezone("America/Sao_Paulo"))).days
        return jsonify({
            "status": "error", 
            "message": f"Você só poderá alterar seus dados novamente em {days_remaining} dias."
        }), 400
    
    # Busca o usuário pelo username atual
    user = get_user_by_username(current_username)
    if not user:
        return jsonify({"status": "error", "message": "Usuário não encontrado."}), 404
    
    # Valida a senha
    if not check_password_hash(user["password_hash"], password):
        return jsonify({"status": "error", "message": "Senha incorreta."}), 400
    
    # Tenta atualizar o username
    success, message = update_username(current_username, new_username)
    
    if success:
        # Atualiza a sessão com o novo username
        session["username"] = new_username
        return jsonify({
            "status": "success",
            "message": message,
            "new_username": new_username
        })
    else:
        return jsonify({
            "status": "error",
            "message": message
        }), 400
