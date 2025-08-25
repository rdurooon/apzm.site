from functools import wraps
from flask import session, redirect, url_for
from routes.register import load_users

def check_user_exists(f):
    """
    Decorator que verifica se o usuário da sessão ainda existe.
    Se não existir, limpa a sessão e redireciona para a página de acesso negado.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" in session:
            users = load_users()
            if not any(u["username"] == session["username"] for u in users):
                session.clear()
                return redirect(url_for("home.session_denied"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorator que exige que o usuário seja admin.
    Se não for, ou se não estiver logado, redireciona para a página de acesso negado.
    """
    @wraps(f)
    @check_user_exists  # primeiro garante que o usuário ainda existe
    def decorated_function(*args, **kwargs):
        username = session.get("username")
        users = load_users()
        user = next((u for u in users if u["username"] == username), None)
        if not user or not user.get("is_admin", False):
            session["is_admin"] = False  # garante que a sessão não engane
            return redirect(url_for("home.session_denied"))
        session["is_admin"] = True
        return f(*args, **kwargs)
    return decorated_function
