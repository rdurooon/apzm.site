import os
import json
from .register import load_users 
from flask import Blueprint, render_template, session, redirect, url_for, send_from_directory, request, jsonify

home_bp = Blueprint("home", __name__)

# ==========================
# Arquivo para salvar status do site
# ==========================
STATUS_FILE = os.path.join("data", "site_status.json")

# ==========================
# Homepage
# ==========================
@home_bp.route("/")
def home():
    # 🔹 Checa se o site está online
    site_online = True
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r") as f:
                site_online = json.load(f).get("online", True)
        except:
            site_online = True

    if not site_online:
        return render_template("off.html")  # template fora do ar

    card_folder = os.path.join('static', 'images', 'cards')
    json_path = os.path.join('data', 'cards.json')

    all_cards = []
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            try:
                all_cards = json.load(f)
            except:
                all_cards = []

    # 🔹 filtra apenas os visíveis
    visible_cards = []
    for card in all_cards:
        card_file = card.get("file")
        is_visible = card.get("visible", True)  # padrão é visível
        if card_file and is_visible and os.path.exists(os.path.join(card_folder, card_file)):
            visible_cards.append({
                "file": card_file,
                "title": card.get("title", "Sem título"),
                "description": card.get("description", ""),
                "visible": True
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
    
    return render_template(
        "home.html",
        cards=visible_cards,
        logged_in=logged_in,
        username=username,
        is_admin=is_admin,
        slide_images=slide_images
    )

# ==========================
# Template sessão negada
# ==========================
@home_bp.route("/session_denied")
def session_denied():
    return render_template("session_denied.html")

# ==========================
# Servir JSONs da pasta data
# ==========================
@home_bp.route("/api/<filename>")
def serve_data(filename):
    return send_from_directory("data", filename)

# ==========================
# Toggle Site Online/Offline
# ==========================
@home_bp.route("/admin/toggle_site", methods=["POST"])
def toggle_site():
    data = request.json
    online = data.get("online", True)
    try:
        with open(STATUS_FILE, "w") as f:
            json.dump({"online": bool(online)}, f)
        return jsonify({"success": True, "online": online})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
