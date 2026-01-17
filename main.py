from flask import Flask, session, redirect, url_for
from routes import registrar_blueprints
from routes.register import load_users


# ========== VERIFICAÇÃO DE SESSÃO ==========
def _verificar_sessao_usuario():
    if "username" not in session:
        return None
    
    usuarios_registrados = load_users() or []
    usuario_existe = any(u.get("username") == session["username"] for u in usuarios_registrados)
    
    if not usuario_existe:
        session.clear()
        return redirect(url_for("home.session_denied"))
    
    return None


# ========== CONFIGURAÇÃO DA APLICAÇÃO ==========
def criar_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'apzm2021'
    
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
