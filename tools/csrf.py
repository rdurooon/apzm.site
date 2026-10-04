import hmac
import secrets

from flask import jsonify, request, session
from tools.db import get_admin_count, get_user_by_username


def get_csrf_token():
    token = session.get("_csrf_token")
    if not isinstance(token, str):
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def has_valid_csrf_token():
    expected = session.get("_csrf_token")
    supplied = request.headers.get("X-CSRF-Token") or request.form.get("_csrf_token")
    return (
        isinstance(expected, str)
        and isinstance(supplied, str)
        and hmac.compare_digest(expected, supplied)
    )


def register_csrf_protection(app):
    @app.before_request
    def protect_csrf():
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return None

        if request.path.startswith("/admin/"):
            username = session.get("username")
            user = get_user_by_username(username) if username else None
            is_admin = bool(user and user.get("is_admin"))
            is_bootstrap_admin = bool(session.get("bootstrap_admin") and get_admin_count() == 0)
            if not is_admin and not is_bootstrap_admin:
                return None

        if request.headers.get("Sec-Fetch-Site") == "cross-site" or not has_valid_csrf_token():
            return jsonify({"status": "error", "message": "Token CSRF ausente ou inválido."}), 400
        return None