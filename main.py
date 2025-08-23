from flask import Flask
from routes import registrar_blueprints

def criar_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'apzm2021'

    registrar_blueprints(app)

    return app

if __name__ == "__main__":
    app = criar_app()
    app.run(debug=True, host='0.0.0.0', port=5000)