from flask import Blueprint, jsonify
from tools.db import list_news as db_list_news
from tools.text_formatter import format_text_to_html

news_bp = Blueprint("news", __name__)

@news_bp.get("/api/news.json")
def api_news():
    news_items = db_list_news()
    formatted_data = []
    for news_item in news_items:
        formatted_item = news_item.copy()
        if "text" in formatted_item:
            formatted_item["text_formatted"] = format_text_to_html(formatted_item.get("text", ""))
        formatted_data.append(formatted_item)

    return jsonify(formatted_data)
