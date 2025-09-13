import os
import json
from flask import (
    Blueprint, render_template, session, redirect, url_for,
    send_from_directory, request, jsonify
)
from .register import load_users
from tools.crypto_utils import decrypt_value

home_bp = Blueprint("home", __name__)

# ==========================
# Constantes
# ==========================
DATA_DIR = "data"
STATIC_DIR = os.path.join("static", "images")

STATUS_FILE = os.path.join(DATA_DIR, "site_status.json")
CARDS_FILE = os.path.join(DATA_DIR, "cards.json")
CARDS_FOLDER = os.path.join(STATIC_DIR, "cards")
BACKGROUND_FOLDER = os.path.join(STATIC_DIR, "background")


# ==========================
# Funções auxiliares
# ==========================
def load_json_file(path, default=None):
    """Carrega JSON de um arquivo, retornando default em caso de erro."""
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def mask_password(password: str) -> str:
    """Retorna a senha mascarada (****)."""
    return "*" * len(password) if password else "********"


def get_visible_cards():
    """Carrega e retorna apenas os cards visíveis com arquivo existente."""
    all_cards = load_json_file(CARDS_FILE, default=[]) or []
    visible_cards = []

    for card in all_cards:
        card_file = card.get("file")
        is_visible = card.get("visible", True)
        if card_file and is_visible and os.path.exists(os.path.join(CARDS_FOLDER, card_file)):
            visible_cards.append({
                "file": card_file,
                "title": card.get("title", "Sem título"),
                "description": card.get("description", ""),
                "visible": True,
                "is_new": card.get("is_new", False),
            })
    return visible_cards


def get_user_from_session():
    """Recupera usuário logado via sessão, ou None."""
    if not session.get("user_logged_in"):
        return None
    username = session.get("username")
    if not username:
        return None

    users = load_users()
    return next((u for u in users if u["username"] == username), None)


# ==========================
# Sitemap
# ==========================
@home_bp.route("/sitemap.xml")
def sitemap():
    return render_template("sitemap.xml"), 200, {"Content-Type": "application/xml"}


# ==========================
# Homepage
# ==========================
@home_bp.route("/")
def home():
    seo = {
        "title": "Amapá Zombies",
        "description": "Descubra o universo de Amapá Zombies: histórias e mapas que se passam no estado do Amapá, baseados no CoD Zombies.",
        "keywords": "Amapá Zombies, Amapá, zombies, zumbis, codzombies",
        "url": "https://amapazombies.com.br/",
        "image": "/static/images/icon.jpg"
    }

    # Status do site
    site_status = load_json_file(STATUS_FILE, default={"online": True})
    if not site_status.get("online", True):
        return render_template("off.html", seo=seo)

    # Cards
    visible_cards = get_visible_cards()

    # Usuário logado
    user = get_user_from_session()
    if user:
        is_admin = user.get("is_admin", False)
        email = decrypt_value(user.get("email", "")) or "não informado"
        raw_password = decrypt_value(user.get("password", "")) or ""
        password_masked = mask_password(raw_password)
        username = user["username"]
    else:
        # se sessão inválida → limpar
        if session.get("user_logged_in"):
            session.clear()
            return redirect(url_for("home.session_denied"))
        username, email, password_masked, is_admin = None, "", "", False

    # Backgrounds
    slide_images = [
        f"/static/images/background/{f}"
        for f in os.listdir(BACKGROUND_FOLDER)
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
    ]

    return render_template(
        "home.html",
        seo=seo,
        cards=visible_cards,
        logged_in=bool(user),
        username=username,
        email=email,
        password_masked=password_masked,
        is_admin=is_admin,
        slide_images=slide_images
    )

# ==========================
# Ratings (Sistema de Estrelas)
# ==========================
RATINGS_FILE = os.path.join(DATA_DIR, "ratings.json")

def load_ratings():
    """Carrega os ratings do arquivo JSON."""
    if not os.path.exists(RATINGS_FILE):
        return {}
    try:
        with open(RATINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_ratings(ratings):
    """Salva os ratings no arquivo JSON."""
    try:
        with open(RATINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(ratings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro ao salvar ratings: {e}")

@home_bp.route("/rate/<item_id>", methods=["POST"])
def rate_item(item_id):
    user = get_user_from_session()
    if not user:
        return jsonify({"success": False, "error": "Usuário não autenticado"}), 401

    data = request.get_json(silent=True) or {}
    rating = int(data.get("rating", 0))
    if rating < 1 or rating > 5:
        return jsonify({"success": False, "error": "Rating inválido"}), 400

    ratings = load_ratings()

    if item_id not in ratings:
        ratings[item_id] = {"usuarios": {}, "media": 0}

    # Atualiza ou cria o voto do usuário
    ratings[item_id]["usuarios"][user["username"]] = rating

    # Recalcula a média
    notas = list(ratings[item_id]["usuarios"].values())
    media = sum(notas) / len(notas)
    ratings[item_id]["media"] = round(media, 2)

    save_ratings(ratings)

    return jsonify({"success": True, "average": ratings[item_id]["media"]})

@home_bp.route("/get_rating/<item_id>")
def get_rating(item_id):
    ratings = load_ratings()
    if item_id in ratings:
        return jsonify(ratings[item_id])
    return jsonify({"usuarios": {}, "media": 0})


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
    return send_from_directory(DATA_DIR, filename)

# ==========================
# Toggle Site Online/Offline
# ==========================
@home_bp.route("/admin/toggle_site", methods=["POST"])
def toggle_site():
    data = request.get_json(silent=True) or {}
    online = data.get("online", True)
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump({"online": bool(online)}, f, ensure_ascii=False)
        return jsonify({"success": True, "online": online})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==========================
# API: Usuário atual
# ==========================
@home_bp.route("/api/current_user")
def current_user():
    user = get_user_from_session()
    if not user:
        return jsonify({"logged_in": False})

    email = decrypt_value(user.get("email", "")) or "não informado"
    raw_password = decrypt_value(user.get("password", "")) or ""
    password_masked = mask_password(raw_password)

    return jsonify({
        "logged_in": True,
        "username": user["username"],
        "email": email,
        "password_masked": password_masked,
        "is_admin": user.get("is_admin", False),
    })
