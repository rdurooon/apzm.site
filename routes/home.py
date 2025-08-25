import os
import json
from .register import load_users 
from flask import Blueprint, render_template, session, redirect, url_for

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
    is_admin = False

    if logged_in and username:
        users = load_users()
        user = next((u for u in users if u["username"] == username), None)
        if user:
            is_admin = user.get("is_admin", False)
        else:
            # Usuário deletado, limpar sessão
            session.clear()
            return redirect(url_for("home.session_denied"))
        
    background_folder = os.path.join('static', 'images', 'background')
    slide_images = [
        f"/static/images/background/{f}" 
        for f in os.listdir(background_folder) 
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
    ]
    
    return render_template("home.html", cards=cards_data, logged_in=logged_in, username=username, is_admin=is_admin, slide_images=slide_images)

@home_bp.route("/session_denied")
def session_denied():
    return render_template("session_denied.html")