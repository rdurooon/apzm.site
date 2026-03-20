import os
import json
from flask import Blueprint, jsonify, current_app
from tools.text_formatter import format_text_to_html

news_bp = Blueprint("news", __name__)

@news_bp.get("/api/news.json")
def api_news():
    # Caminho absoluto seguro a partir do root do projeto
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    news_path = os.path.join(base_dir, "data", "news.json")

    if not os.path.exists(news_path):
        with open(news_path, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)
        return jsonify([])

    try:
        with open(news_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Garantia: sempre lista
        if not isinstance(data, list):
            return jsonify([])

        # Formatar texto das notícias
        formatted_data = []
        for news_item in data:
            formatted_item = news_item.copy()
            if "text" in formatted_item:
                formatted_item["text_formatted"] = format_text_to_html(formatted_item.get("text", ""))
            formatted_data.append(formatted_item)

        return jsonify(formatted_data)
    except Exception:
        # Em produção, você pode logar isso
        return jsonify([]), 200
