import os
import json
from flask import Blueprint, jsonify, current_app

news_bp = Blueprint("news", __name__)

@news_bp.get("/api/news.json")
def api_news():
    # Caminho absoluto seguro a partir do root do projeto
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    news_path = os.path.join(base_dir, "data", "news.json")

    if not os.path.exists(news_path):
        return jsonify([])

    try:
        with open(news_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Garantia: sempre lista
        if not isinstance(data, list):
            return jsonify([])

        return jsonify(data)
    except Exception:
        # Em produção, você pode logar isso
        return jsonify([]), 200
