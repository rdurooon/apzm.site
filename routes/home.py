import os
import json
from flask import Blueprint, render_template, session

home_bp = Blueprint("home", __name__)

@home_bp.route("/")
def home():
    card_folder = os.path.join('static', 'images', 'cards')
    json_path = os.path.join('data', 'cards.json')

    cards_data = []
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            all_cards = json.load(f)
            for card in all_cards:
                card_file = card.get("file")
                if card_file and os.path.exists(os.path.join(card_folder, card_file)):
                    cards_data.append({
                        "file": card_file,
                        "title": card.get("title", "Sem título"),
                        "description": card.get("description", "")
                    })

    # Verifica se usuário está logado
    logged_in = session.get("user_logged_in", False)
    username = session.get("username") if logged_in else None

    return render_template("home.html", cards=cards_data, logged_in=logged_in, username=username)