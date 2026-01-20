from .home import home_bp
from .admin import admin_bp
from .register import register_bp
from .auth import auth_bp
from .email import email_bp
from .news import news_bp

def registrar_blueprints(app):
    app.register_blueprint(home_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(register_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(email_bp)
    app.register_blueprint(news_bp)