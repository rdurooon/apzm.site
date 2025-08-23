from .home import home_bp

def registrar_blueprints(app):
    app.register_blueprint(home_bp)