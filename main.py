from flask import Flask, session, redirect, url_for
from routes import registrar_blueprints
from routes.register import load_users
import os

def criar_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'apzm2021'

    registrar_blueprints(app)

    # ==================== CACHE-BUSTING SEGURO PARA CSS/JS ====================
    # @app.context_processor
    # def override_url_for():
    #     def dated_url_for(endpoint, **values):
    #         if endpoint == 'static':
    #             filename = values.get('filename')
    #             if filename:
    #                 Aplica apenas para CSS ou JS nas pastas corretas
    #                 if filename.startswith("css/"):
    #                     file_path = os.path.join(app.root_path, 'static', filename)
    #                     if os.path.exists(file_path):
    #                         values['v'] = int(os.path.getmtime(file_path))
    #         return url_for(endpoint, **values)
    #     return dict(url_for=dated_url_for)

    # ==================== VERIFICAÇÃO DE SESSÃO ====================
    @app.before_request
    def verify_user_session():
        if "username" in session:
            users = load_users() or []
            if not any(u.get("username") == session["username"] for u in users):
                session.clear()
                return redirect(url_for("home.session_denied"))

    return app

if __name__ == "__main__":
    app = criar_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
