from functools import wraps
from flask import session, redirect, url_for
from tools.db import get_admin_count, get_user_by_username

def check_user_exists(f):
    """
    Decorator que verifica se o usuário da sessão ainda existe.
    Se não existir, limpa a sessão e redireciona para a página de acesso negado.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        username = session.get("username")
        if username:
            user = get_user_by_username(username)
            if not user:
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
    @check_user_exists
    def decorated_function(*args, **kwargs):
        username = session.get("username")
        user = get_user_by_username(username) if username else None
        if not user or not user.get("is_admin", False):
            if session.get("bootstrap_admin") and get_admin_count() == 0:
                session["is_admin"] = True
                return f(*args, **kwargs)
            session["is_admin"] = False
            return redirect(url_for("home.session_denied"))
        session["is_admin"] = True
        return f(*args, **kwargs)
    return decorated_function
