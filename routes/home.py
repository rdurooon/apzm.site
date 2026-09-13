import os
import re
import unicodedata
from flask import (
    Blueprint, render_template, session, redirect, url_for,
    request, jsonify, send_file
)
from tools.db import (
    get_user_by_username,
    set_user_over18 as db_set_user_over18,
    get_visible_cards as db_get_visible_cards,
    get_partners as db_get_partners,
    get_site_status,
    set_site_status,
    increment_site_visits,
    get_comments_for_card,
    add_or_update_comment,
    delete_comment as db_delete_comment,
    get_likes_for_card,
    toggle_like_card,
    get_card_links,
    get_story_by_slug,
    get_story_slugs,
    get_card_by_file,
    get_story_pdf as db_get_story_pdf,
)
from tools.crypto_utils import decrypt_value
from tools.text_formatter import format_text_to_html

home_bp = Blueprint("home", __name__)

# ==================== CONSTANTES ====================
STATIC_DIR = os.path.join("static", "images")
CARDS_FOLDER = os.path.join(STATIC_DIR, "cards")
BACKGROUND_FOLDER = os.path.join(STATIC_DIR, "background")
STORY_PDF_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "story_pdfs"))


def story_pdf_path(stored_filename):
    if not re.fullmatch(r"[a-f0-9]{32}\.pdf", stored_filename or ""):
        return None
    return os.path.join(STORY_PDF_DIR, stored_filename)

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


def slugify(text: str) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = normalized.strip("-")
    return normalized


def parse_story_content(raw_text: str):
    if not raw_text:
        return []

    lines = raw_text.splitlines()
    chapters = []
    current = None
    paragraph_buffer = []

    def flush_paragraph():
        nonlocal paragraph_buffer
        if paragraph_buffer and current is not None:
            paragraph = "\n".join(p.strip() for p in paragraph_buffer).strip()
            if paragraph:
                current["paragraphs"].append(format_text_to_html(paragraph))
            paragraph_buffer = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            if current is not None:
                flush_paragraph()
                chapters.append(current)
            title = stripped.lstrip("#").strip() or "Capítulo"
            current = {"title": title, "paragraphs": []}
        else:
            if current is not None:
                if stripped == "":
                    flush_paragraph()
                else:
                    paragraph_buffer.append(stripped)

    if current is not None:
        flush_paragraph()
        chapters.append(current)

    return chapters


def resolve_story_hero_image(card_file: str, stored_hero_image: str | None):
    if stored_hero_image:
        stored_path = os.path.join(STATIC_DIR, 'covers', stored_hero_image)
        if os.path.exists(stored_path):
            return url_for('static', filename=f'images/covers/{stored_hero_image}')
        # backward compatibility only when the cover was previously stored in titles
        stored_path = os.path.join(STATIC_DIR, 'titles', stored_hero_image)
        if os.path.exists(stored_path):
            return url_for('static', filename=f'images/titles/{stored_hero_image}')

    return None


def resolve_card_title_image(card_file: str):
    """Resolve the title image (used as the card/story title graphic) from the titles folder.

    This must not be mixed with the story cover/background which lives in `covers/`.
    """
    base_name = os.path.splitext(card_file)[0]
    for ext in ('png', 'jpg', 'jpeg', 'webp'):
        candidate = os.path.join(STATIC_DIR, 'titles', f'{base_name}.{ext}')
        if os.path.exists(candidate):
            return url_for('static', filename=f'images/titles/{base_name}.{ext}')
    return None


def parse_story_body(raw_text: str):
    if not raw_text:
        return []

    paragraphs = []
    buffer = []

    for line in raw_text.splitlines():
        stripped = line.strip()
        if stripped == "":
            if buffer:
                paragraph = "\n".join(p.strip() for p in buffer).strip()
                if paragraph:
                    paragraphs.append(format_text_to_html(paragraph))
                buffer = []
        else:
            buffer.append(stripped)

    if buffer:
        paragraph = "\n".join(p.strip() for p in buffer).strip()
        if paragraph:
            paragraphs.append(format_text_to_html(paragraph))

    return paragraphs


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

    increment_site_visits()

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


@home_bp.route("/historia/<slug>")
def historia(slug):
    story = get_story_by_slug(slug, public_view=True)
    if not story:
        seo = {
            "title": "História não encontrada - Amapá Zombies",
            "description": "A história requisitada não foi encontrada.",
            "keywords": "história não encontrada, Amapá Zombies",
            "url": f"https://amapazombies.com.br/historia/{slug}",
            "image": "/static/images/icon.jpg"
        }
        return render_template("historia.html", seo=seo, story=None), 404

    card = get_card_by_file(story["card_file"])
    # hero_cover is the background image for the story page (uploaded in Escrever/Revisar -> /covers)
    hero_cover = resolve_story_hero_image(story["card_file"], story.get("hero_image"))
    # title_image is the card title graphic stored in /titles and must be shown in front of the hero background
    title_image = resolve_card_title_image(story["card_file"]) if card and card.get("file") else None
    # legacy behavior: if no cover was uploaded and the card has an image, fall back to the card image (small)
    card_cover_fallback = None
    if card and card.get("file"):
        cover_path = os.path.join(CARDS_FOLDER, card["file"])
        if os.path.exists(cover_path):
            card_cover_fallback = url_for('static', filename=f'images/cards/{card["file"]}')

    raw_content = story.get("content", "")
    chapters = parse_story_content(raw_content)
    body_paragraphs = [] if chapters else parse_story_body(raw_content)
    title = card["title"] if card else story.get("slug", slug)
    pdf = db_get_story_pdf(story["card_file"])
    pdf_available = bool(pdf and story_pdf_path(pdf["stored_filename"]) and os.path.isfile(story_pdf_path(pdf["stored_filename"])))

    seo = {
        "title": f"{title} - História | Amapá Zombies",
        "description": f"Leia a história de {title} diretamente no site Amapá Zombies.",
        "keywords": f"Amapá Zombies, {title}, história, leitura",
        "url": f"https://amapazombies.com.br/historia/{slug}",
        "image": "/static/images/icon.jpg"
    }

    return render_template(
        "historia.html",
        seo=seo,
        story={
            "slug": slug,
            "title": title,
            "chapters": chapters,
            "body_paragraphs": body_paragraphs,
            # `hero_image` in the template is the title graphic (from /titles)
            "hero_image": title_image,
            # `cover_image` in the template is the large background (from /covers or fallback to card image)
            "cover_image": hero_cover or card_cover_fallback,
            "card_file": story["card_file"],
            "pdf_available": pdf_available,
        }
    )


@home_bp.route("/historia/<slug>/baixar")
def download_story_pdf(slug):
    story = get_story_by_slug(slug, public_view=True)
    if not story:
        return redirect(url_for("home.session_denied"))
    pdf = db_get_story_pdf(story["card_file"])
    if not pdf:
        return redirect(url_for("home.session_denied"))
    pdf_path = story_pdf_path(pdf["stored_filename"])
    if not pdf_path or not os.path.isfile(pdf_path):
        return redirect(url_for("home.session_denied"))
    return send_file(
        pdf_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"APZM-{pdf['original_filename']}"
    )


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
    raw_comment = data.get("comment", "") or ""
    comment_text = raw_comment.strip()
    if not comment_text:
        return jsonify({"status": "error", "message": "Comentário vazio"}), 400

    comment_text = comment_text.replace("\x00", "")
    comment_text = "".join(ch for ch in comment_text if ch.isprintable() or ch in "\n\t")
    comment_text = comment_text[:120]

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


# ==================== API DADOS ====================
@home_bp.route("/api/<filename>")
def serve_data(filename):
    if filename == "site_status.json":
        return jsonify({"online": get_site_status()})
    if filename == "links.json":
        links = get_card_links()
        story_slugs = get_story_slugs()
        for card_file, slug in story_slugs.items():
            if card_file not in links:
                links[card_file] = {}
            links[card_file]["story_slug"] = slug
        return jsonify(links)
    return jsonify({"error": "Endpoint não encontrado."}), 404


# ==================== API ADMIN ====================
@home_bp.route("/admin/toggle_site", methods=["POST"])
def toggle_site():
    data = request.get_json(silent=True) or {}
    online = data.get("online", True)
    set_site_status(bool(online))
    return jsonify({"success": True, "online": bool(online)})