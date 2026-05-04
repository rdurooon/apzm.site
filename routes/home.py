import os
from flask import (
    Blueprint, render_template, session, redirect, url_for,
    request, jsonify
)
from tools.db import (
    get_user_by_username,
    set_user_over18 as db_set_user_over18,
    get_visible_cards as db_get_visible_cards,
    get_partners as db_get_partners,
    get_site_status,
    get_comments_for_card,
    add_or_update_comment,
    delete_comment as db_delete_comment,
    get_likes_for_card,
    toggle_like_card,
    set_rating,
    get_rating_for_item,
    get_card_links,
)
from tools.crypto_utils import decrypt_value
from tools.text_formatter import format_text_to_html

home_bp = Blueprint("home", __name__)

# ==================== CONSTANTES ====================
STATIC_DIR = os.path.join("static", "images")
CARDS_FOLDER = os.path.join(STATIC_DIR, "cards")
BACKGROUND_FOLDER = os.path.join(STATIC_DIR, "background")

# ==================== UTILITÁRIOS ====================
def mask_password(password: str) -> str:
    return "*" * len(password) if password else "********"


def get_user_from_session():
    username = session.get("username")
    if not username:
        return None
    return get_user_by_username(username)


def set_user_over18(username, is_over18):
    return db_set_user_over18(username, bool(is_over18))


def get_visible_cards():
    all_cards = db_get_visible_cards() or []
    visible_cards = []
    for card in all_cards:
        card_file = card.get("file")
        if card_file and os.path.exists(os.path.join(CARDS_FOLDER, card_file)):
            visible_cards.append({
                "file": card_file,
                "title": card.get("title", "Sem título"),
                "description": card.get("description", ""),
                "description_formatted": format_text_to_html(card.get("description", "")),
                "visible": True,
                "is_new": bool(card.get("is_new", False)),
            })
    return visible_cards


def load_parceiros():
    parceiros = db_get_partners() or []
    return [
        {
            "nome": p.get("nome", "Sem nome"),
            "file": p.get("file", ""),
            "descricao": p.get("descricao", ""),
            "site": p.get("site", ""),
            "instagram": p.get("instagram", ""),
            "twitter": p.get("twitter", ""),
            "discord": p.get("discord", ""),
            "email": p.get("email", ""),
        }
        for p in parceiros
    ]


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

    if not get_site_status():
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

    email = decrypt_value(user.get("email_encrypted", "")) or "não informado"
    return jsonify({
        "logged_in": True,
        "username": user["username"],
        "email": email,
        "password_masked": mask_password(None),
        "is_admin": bool(user.get("is_admin", False)),
        "is_over_18": bool(user.get("is_over_18", False)),
    })


@home_bp.route("/api/set_over18", methods=["POST"])
def set_over18():
    user = get_user_from_session()
    if not user:
        return jsonify({"status": "error", "message": "Usuário não autenticado."}), 401

    data = request.get_json(silent=True) or {}
    is_over18 = data.get("isOver18")
    if is_over18 is None:
        return jsonify({"status": "error", "message": "Parâmetro isOver18 obrigatório."}), 400

    if not set_user_over18(user.get("username"), bool(is_over18)):
        return jsonify({"status": "error", "message": "Não foi possível atualizar o usuário."}), 500

    return jsonify({"status": "success", "message": "Verificação de idade atualizada."})


# ==================== API COMENTÁRIOS ====================
@home_bp.route("/api/comments/<card_id>", methods=["GET"])
def get_comments(card_id):
    return jsonify(get_comments_for_card(card_id) or {})


@home_bp.route("/api/comments/<card_id>", methods=["POST"])
def add_comment(card_id):
    user = get_user_from_session()
    if not user:
        return jsonify({"status": "error", "message": "Usuário não autenticado"}), 401

    data = request.get_json(silent=True) or {}
    comment_text = data.get("comment", "").strip()
    if not comment_text:
        return jsonify({"status": "error", "message": "Comentário vazio"}), 400

    add_or_update_comment(card_id, user["username"], comment_text)
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

    comments = get_comments_for_card(card_id) or {}
    if target_user not in comments:
        return jsonify({"status": "error", "message": "Comentário não encontrado"}), 404

    if user["username"] != target_user and not user.get("is_admin", False):
        return jsonify({"status": "error", "message": "Permissão negada"}), 403

    db_delete_comment(card_id, target_user)
    return jsonify({"status": "success", "message": "Comentário deletado."})


# ==================== API LIKES ====================
@home_bp.route("/get_likes/<filename>")
def get_likes(filename):
    user = get_user_from_session()
    username = user["username"] if user else None

    likes, liked = get_likes_for_card(filename, username)
    return jsonify({
        "likes": likes,
        "user_liked": liked
    })


@home_bp.route("/like/<filename>", methods=["POST"])
def like_card(filename):
    user = get_user_from_session()
    if not user:
        return jsonify({"status": "error", "message": "Necessário login"}), 403

    username = user["username"]
    action, likes = toggle_like_card(filename, username)
    return jsonify({
        "status": "success",
        "likes": likes,
        "action": action
    })


# ==================== API RATINGS ====================
@home_bp.route("/rate/<item_id>", methods=["POST"])
def rate_item(item_id):
    user = get_user_from_session()
    if not user:
        return jsonify({"success": False, "error": "Usuário não autenticado"}), 401

    data = request.get_json(silent=True) or {}
    try:
        rating = int(data.get("rating", 0))
    except (TypeError, ValueError):
        rating = 0

    if rating < 1 or rating > 5:
        return jsonify({"success": False, "error": "Rating inválido"}), 400

    rating_data = set_rating(item_id, user["username"], rating)
    return jsonify({"success": True, "average": rating_data.get("media", 0)})


@home_bp.route("/get_rating/<item_id>")
def get_rating(item_id):
    return jsonify(get_rating_for_item(item_id))


# ==================== API DADOS ====================
@home_bp.route("/api/<filename>")
def serve_data(filename):
    if filename == "site_status.json":
        return jsonify({"online": get_site_status()})
    if filename == "links.json":
        return jsonify(get_card_links())
    return jsonify({"error": "Endpoint não encontrado."}), 404


# ==================== API ADMIN ====================
@home_bp.route("/admin/toggle_site", methods=["POST"])
def toggle_site():
    data = request.get_json(silent=True) or {}
    online = data.get("online", True)
    set_site_status(bool(online))
    return jsonify({"success": True, "online": bool(online)})