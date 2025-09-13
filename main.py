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
        Substitui url_for para adicionar timestamp nos arquivos estáticos
        e evitar problemas de cache do navegador
        """
        return dict(url_for=dated_url_for)

    def dated_url_for(endpoint, **values):
        if endpoint == 'static':
            filename = values.get('filename', None)
            if filename:
                file_path = os.path.join(app.root_path, 'static', filename)
                if os.path.exists(file_path):
                    # Adiciona timestamp do último modificado como query string
                    values['v'] = int(os.path.getmtime(file_path))
        return url_for(endpoint, **values)

    # ==================== VERIFICAÇÃO DE SESSÃO ====================
    @app.before_request
    def verify_user_session():
        if "username" in session:
            users = load_users()
            # Se o usuário da sessão não existir mais, limpa a sessão e envia para acesso negado
            if not any(u["username"] == session["username"] for u in users):
                session.clear()
                return redirect(url_for("home.session_denied"))

    return app

if __name__ == "__main__":
    app = criar_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
