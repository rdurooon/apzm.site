from flask import Flask, session, redirect, url_for
from routes import registrar_blueprints
from routes.register import load_users
import os

def criar_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'apzm2021'

    registrar_blueprints(app)

    # ==================== VERIFICAÇÃO DE SESSÃO ====================
    @app.before_request
    def verify_user_session():
        if "username" in session:
            users = load_users() or []
            if not any(u.get("username") == session["username"] for u in users):
                session.clear()
                return redirect(url_for("home.session_denied"))

    return app

# ===============================
# Cria app global para Gunicorn
# ===============================
app = criar_app()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
