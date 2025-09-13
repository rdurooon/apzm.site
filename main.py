from flask import Flask, session, redirect, url_for
from routes import registrar_blueprints
from routes.register import load_users
import os

def criar_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'apzm2021'

    registrar_blueprints(app)

    # ==================== CACHE-BUSTING AUTOMÁTICO ====================
    @app.context_processor
    def override_url_for():
        """
        Substitui url_for nos templates para adicionar timestamp nos arquivos estáticos
        e evitar problemas de cache do navegador, sem quebrar paths diretos.
        """
        def dated_url_for(endpoint, **values):
            if endpoint == 'static':
                filename = values.get('filename')
                if filename:
                    file_path = os.path.join(app.root_path, 'static', filename)
                    if os.path.exists(file_path):
                        try:
                            values['v'] = int(os.path.getmtime(file_path))
                        except Exception:
                            pass  # Se houver erro, ignora e mantém URL normal
            return url_for(endpoint, **values)

        return dict(url_for=dated_url_for)

    # ==================== VERIFICAÇÃO DE SESSÃO ====================
    @app.before_request
    def verify_user_session():
        if "username" in session:
            users = load_users() or []
            # Se o usuário da sessão não existir mais, limpa a sessão e envia para acesso negado
            if not any(u.get("username") == session["username"] for u in users):
                session.clear()
                return redirect(url_for("home.session_denied"))

    return app

if __name__ == "__main__":
    app = criar_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
