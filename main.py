from flask import Flask, session, redirect, url_for
from secrets import token_urlsafe
from routes import registrar_blueprints
from tools.db import init_app, get_admin_count, get_user_by_username


# ========== VERIFICAÇÃO DE SESSÃO ==========
def _verificar_sessao_usuario():
    if "username" not in session:
        return None

    usuario_existe = get_user_by_username(session["username"]) is not None
    if not usuario_existe:
        session.clear()
        return redirect(url_for("home.session_denied"))

    return None


# ========== CONFIGURAÇÃO DA APLICAÇÃO ==========
def _init_bootstrap_admin(app):
    with app.app_context():
        if get_admin_count() == 0:
            token = token_urlsafe(24)
            app.config["BOOTSTRAP_ADMIN_TOKEN"] = token
            app.config["BOOTSTRAP_ADMIN_TOKEN_USED"] = False
            print(f"Bootstrap admin access available at http://127.0.0.1:5000/admin_access/{token}")
        else:
            app.config["BOOTSTRAP_ADMIN_TOKEN"] = None
            app.config["BOOTSTRAP_ADMIN_TOKEN_USED"] = True


def criar_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'apzm2021'

    init_app(app)
    _init_bootstrap_admin(app)

    # Carrega as rotas
    registrar_blueprints(app)
    
    # Middleware de autenticação
    app.before_request(_verificar_sessao_usuario)

    return app


# ========== INSTÂNCIA GLOBAL ==========
app = criar_app()


# ========== EXECUÇÃO LOCAL ==========
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
