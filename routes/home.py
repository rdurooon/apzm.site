import os
import json
from flask import (
    Blueprint, render_template, session, redirect, url_for,
    send_from_directory, request, jsonify
)
from .register import load_users
from tools.crypto_utils import decrypt_value

home_bp = Blueprint("home", __name__)

# ==================== CONSTANTES ====================
DATA_DIR = "data"
STATIC_DIR = os.path.join("static", "images")

STATUS_FILE = os.path.join(DATA_DIR, "site_status.json")
CARDS_FILE = os.path.join(DATA_DIR, "cards.json")
COMMENTS_FILE = os.path.join(DATA_DIR, "comments.json")
PARCEIROS_FILE = os.path.join(DATA_DIR, "parceiros.json")
RATINGS_FILE = os.path.join(DATA_DIR, "ratings.json")
LIKES_FILE = os.path.join(DATA_DIR, "likes.json")

CARDS_FOLDER = os.path.join(STATIC_DIR, "cards")
BACKGROUND_FOLDER = os.path.join(STATIC_DIR, "background")

# ==================== UTILITÁRIOS ====================
def load_json_file(path, default=None):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json_file(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erro ao salvar {path}: {e}")
        return False


def mask_password(password: str) -> str:
    return "*" * len(password) if password else "********"


def get_user_from_session():
    username = session.get("username")
    if not username:
        return None
    users = load_users()
    return next((u for u in users if u.get("username") == username), None)


def get_visible_cards():
    all_cards = load_json_file(CARDS_FILE, default=[]) or []
    visible_cards = []
    for card in all_cards:
        card_file = card.get("file")
        if card_file and card.get("visible", True) and os.path.exists(os.path.join(CARDS_FOLDER, card_file)):
            visible_cards.append({
                "file": card_file,
                "title": card.get("title", "Sem título"),
                "description": card.get("description", ""),
                "visible": True,
                "is_new": card.get("is_new", False),
            })
    return visible_cards


def load_parceiros():
    parceiros = load_json_file(PARCEIROS_FILE, default=[]) or []
    return [{
        "nome": p.get("nome", "Sem nome"),
        "file": p.get("file", ""),
        "descricao": p.get("descricao", ""),
        "site": p.get("site", ""),
        "instagram": p.get("instagram", ""),
        "twitter": p.get("twitter", ""),
        "email": p.get("email", ""),
    } for p in parceiros]


# ==================== CACHE CONTROL ====================
@home_bp.after_request
def add_no_cache_headers(response):
    if request.path.startswith(("/api/", "/get_", "/rate")):  
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# ==================== RENDERIZAÇÃO ====================
@home_bp.route("/sitemap.xml")
def sitemap():
    return render_template("sitemap.xml"), 200, {"Content-Type": "application/xml"}


@home_bp.route("/")
def home():
    seo = {
        "title": "Amapá Zombies",
        "description": "Descubra o universo de Amapá Zombies: histórias e mapas que se passam no estado do Amapá, baseados no CoD Zombies.",
        "keywords": "Amapá Zombies, Amapá, zombies, zumbis, codzombies",
        "url": "https://amapazombies.com.br/",
        "image": "/static/images/icon.jpg"
    }

    site_status = load_json_file(STATUS_FILE, default={"online": True})
    if not site_status.get("online", True):
        return render_template("off.html", seo=seo)

    visible_cards = get_visible_cards()
    user = get_user_from_session()

    if user:
        email = decrypt_value(user.get("email", "")) or "não informado"
        raw_password = decrypt_value(user.get("password", "")) or ""
        password_masked = mask_password(raw_password)
    else:
        if session.get("user_logged_in"):
            session.clear()
            return redirect(url_for("home.session_denied"))
        email, password_masked = "", ""

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
        username=user["username"] if user else None,
        email=email,
        password_masked=password_masked,
        is_admin=user.get("is_admin", False) if user else False,
        slide_images=slide_images,
        parceiros=load_parceiros()
    )


@home_bp.route("/session_denied")
def session_denied():
    return render_template("session_denied.html")


# ==================== API USUÁRIO ====================
@home_bp.route("/api/current_user")
def current_user():
    user = get_user_from_session()
    if not user:
        return jsonify({"logged_in": False})

    email = decrypt_value(user.get("email", "")) or "não informado"
    raw_password = decrypt_value(user.get("password", "")) or ""

    return jsonify({
        "logged_in": True,
        "username": user["username"],
        "email": email,
        "password_masked": mask_password(raw_password),
        "is_admin": user.get("is_admin", False),
    })


# ==================== API COMENTÁRIOS ====================
@home_bp.route("/api/comments/<card_id>", methods=["GET"])
def get_comments(card_id):
    comments = load_json_file(COMMENTS_FILE, default={})
    return jsonify(comments.get(card_id, {}))


@home_bp.route("/api/comments/<card_id>", methods=["POST"])
def add_comment(card_id):
    user = get_user_from_session()
    if not user:
        return jsonify({"status": "error", "message": "Usuário não autenticado"}), 401

    data = request.get_json(silent=True) or {}
    comment_text = data.get("comment", "").strip()
    if not comment_text:
        return jsonify({"status": "error", "message": "Comentário vazio"}), 400

    comments = load_json_file(COMMENTS_FILE, default={})
    if card_id not in comments:
        comments[card_id] = {}

    comments[card_id][user["username"]] = comment_text
    save_json_file(COMMENTS_FILE, comments)

    return jsonify({"status": "success", "message": "Comentário adicionado!"})


@home_bp.route("/api/delete_comment", methods=["POST"])
def delete_comment():
    user = get_user_from_session()
    if not user:
        return jsonify({"status": "error", "message": "Usuário não autenticado"}), 401

    data = request.get_json(silent=True) or {}
    card_id = data.get("card")
    target_user = data.get("user")

    if not card_id or not target_user:
        return jsonify({"status": "error", "message": "Dados insuficientes"}), 400

    comments = load_json_file(COMMENTS_FILE, default={})
    if card_id not in comments or target_user not in comments[card_id]:
        return jsonify({"status": "error", "message": "Comentário não encontrado"}), 404

    if user["username"] != target_user and not user.get("is_admin", False):
        return jsonify({"status": "error", "message": "Permissão negada"}), 403

    del comments[card_id][target_user]
    if not comments[card_id]:
        del comments[card_id]

    save_json_file(COMMENTS_FILE, comments)
    return jsonify({"status": "success", "message": "Comentário deletado."})


# ==================== API LIKES ====================
@home_bp.route("/get_likes/<filename>")
def get_likes(filename):
    user = get_user_from_session()
    username = user["username"] if user else None

    likes_data = load_json_file(LIKES_FILE, default={})
    card_likes = likes_data.get(filename, {"likes": 0, "liked_by": []})

    return jsonify({
        "likes": card_likes.get("likes", 0),
        "user_liked": username in card_likes.get("liked_by", []) if username else False
    })


@home_bp.route("/like/<filename>", methods=["POST"])
def like_card(filename):
    user = get_user_from_session()
    if not user:
        return jsonify({"status": "error", "message": "Necessário login"}), 403

    username = user["username"]
    likes_data = load_json_file(LIKES_FILE, default={})
    card_likes = likes_data.get(filename, {"likes": 0, "liked_by": []})

    if username in card_likes["liked_by"]:
        card_likes["liked_by"].remove(username)
        card_likes["likes"] -= 1
        action = "unliked"
    else:
        card_likes["liked_by"].append(username)
        card_likes["likes"] += 1
        action = "liked"

    likes_data[filename] = card_likes
    save_json_file(LIKES_FILE, likes_data)

    return jsonify({
        "status": "success",
        "likes": card_likes["likes"],
        "action": action
    })


# ==================== API RATINGS ====================
@home_bp.route("/rate/<item_id>", methods=["POST"])
def rate_item(item_id):
    user = get_user_from_session()
    if not user:
        return jsonify({"success": False, "error": "Usuário não autenticado"}), 401

    data = request.get_json(silent=True) or {}
    rating = int(data.get("rating", 0))
    if rating < 1 or rating > 5:
        return jsonify({"success": False, "error": "Rating inválido"}), 400

    ratings = load_json_file(RATINGS_FILE, default={})
    if item_id not in ratings:
        ratings[item_id] = {"usuarios": {}, "media": 0}

    ratings[item_id]["usuarios"][user["username"]] = rating
    notas = list(ratings[item_id]["usuarios"].values())
    ratings[item_id]["media"] = round(sum(notas) / len(notas), 2)

    save_json_file(RATINGS_FILE, ratings)
    return jsonify({"success": True, "average": ratings[item_id]["media"]})


@home_bp.route("/get_rating/<item_id>")
def get_rating(item_id):
    ratings = load_json_file(RATINGS_FILE, default={})
    return jsonify(ratings.get(item_id, {"usuarios": {}, "media": 0}))


# ==================== API DADOS ====================
@home_bp.route("/api/<filename>")
def serve_data(filename):
    return send_from_directory(DATA_DIR, filename)


# ==================== API ADMIN ====================
@home_bp.route("/admin/toggle_site", methods=["POST"])
def toggle_site():
    data = request.get_json(silent=True) or {}
    online = data.get("online", True)
    if save_json_file(STATUS_FILE, {"online": bool(online)}):
        return jsonify({"success": True, "online": online})
    return jsonify({"success": False, "error": "Erro ao salvar"}), 500