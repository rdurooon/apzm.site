from datetime import datetime, timedelta
import pytz
import os
import shutil
from flask import Blueprint, render_template, jsonify, request, current_app, redirect, url_for, session
from werkzeug.utils import secure_filename
from .register import promote_user, demote_user, delete_user
from tools.decorators import admin_required
from tools.db import (
    get_admin_count as db_get_admin_count,
    get_all_users,
    get_cards as db_get_cards,
    get_card_links as db_get_card_links,
    insert_card as db_insert_card,
    delete_card as db_delete_card,
    update_cards_order as db_update_cards_order,
    update_card as db_update_card,
    save_card_links as db_save_card_links,
    get_partners as db_get_partners,
    insert_news as db_insert_news,
    list_news as db_list_news,
    get_news_item as db_get_news_item,
    update_news as db_update_news,
    delete_news as db_delete_news,
    check_new_badges as db_check_new_badges,
)

admin_bp = Blueprint("admin", __name__)

# =========================== CONSTANTES ===========================
CARD_DIR = "static/images/cards/"
TITLE_DIR = "static/images/titles/"
NEWS_DIR = "static/images/news/"

# =========================== FUNÇÃO PARA CHECAR "NOVA" ===========================
def check_new_badges(cards):
    return db_check_new_badges(cards)


# =========================== ROTA PRINCIPAL ===========================
@admin_bp.route("/admin")
@admin_required
def admin():
    return render_template("admin.html")


@admin_bp.route("/admin_access/<token>")
def admin_access(token):
    if db_get_admin_count() > 0:
        return redirect(url_for("home.session_denied"))

    expected = current_app.config.get("BOOTSTRAP_ADMIN_TOKEN")
    used = current_app.config.get("BOOTSTRAP_ADMIN_TOKEN_USED", False)
    if not expected or used or token != expected:
        return redirect(url_for("home.session_denied"))

    session["bootstrap_admin"] = True
    session["is_admin"] = True
    current_app.config["BOOTSTRAP_ADMIN_TOKEN_USED"] = True
    return redirect(url_for("admin.admin"))


# =========================== LISTAR USUÁRIOS ===========================
@admin_bp.route("/admin/list_users")
@admin_required
def list_users():
    users = get_all_users()
    return jsonify([
        {
            "id": u["id"],
            "username": u["username"],
            "is_admin": u.get("is_admin", False),
            "created_at": u.get("created_at", "Desconhecido")
        }
        for u in users
    ])


# =========================== LISTAR LINKS ===========================
@admin_bp.route("/admin/list_links")
@admin_required
def list_links():
    cards = db_get_cards()
    links_data = db_get_card_links()

    for card in cards:
        file = card["file"]
        card_links = links_data.get(file, {})
        card["link_historia"] = card_links.get("historia", "")
        card["link_mapa"] = card_links.get("mapa", "")

    return jsonify(cards)


# =========================== PROMOVER/DEMOVER/DELETAR USUÁRIO ===========================
@admin_bp.route("/admin/promote/<user_id>", methods=["POST"])
@admin_required
def promote(user_id):
    return jsonify({"success": promote_user(user_id)})


@admin_bp.route("/admin/demote/<user_id>", methods=["POST"])
@admin_required
def demote(user_id):
    return jsonify({"success": demote_user(user_id)})


@admin_bp.route("/admin/delete/<user_id>", methods=["DELETE"])
@admin_required
def delete(user_id):
    return jsonify({"success": delete_user(user_id)})


# =========================== LISTAR CARDS ===========================
@admin_bp.route("/admin/list_cards")
@admin_required
def list_cards():
    cards = db_get_cards()
    cards = check_new_badges(cards)
    return jsonify(cards)


# =========================== ADICIONAR MAPA/HISTÓRIA ===========================
@admin_bp.route("/admin/add_map_story", methods=["POST"])
@admin_required
def add_map_story():
    description = request.form.get("description")
    title_text = request.form.get("title_text")
    card_image = request.files.get("card_image")

    if not description or not title_text or not card_image:
        return jsonify({"success": False, "error": "Faltando descrição, título ou imagem do card"})

    # Salva imagem do card
    os.makedirs(CARD_DIR, exist_ok=True)
    card_filename = secure_filename(card_image.filename) # type: ignore
    card_path = os.path.join(CARD_DIR, card_filename)
    card_image.save(card_path)

    # Salva imagem do título (ou usa o mesmo arquivo do card)
    os.makedirs(TITLE_DIR, exist_ok=True)
    title_image = request.files.get("title_image")
    if title_image:
        title_filename = secure_filename(title_image.filename) # type: ignore
        title_path = os.path.join(TITLE_DIR, title_filename)
        title_image.save(title_path)
    else:
        title_filename = card_filename
        title_path = os.path.join(TITLE_DIR, title_filename)
        shutil.copy(card_path, title_path)

    db_insert_card(card_filename, title_text, description)
    return jsonify({"success": True})


# =========================== REMOVER MAPA/HISTÓRIA ===========================
@admin_bp.route("/admin/delete_map_story/<filename>", methods=["DELETE"])
@admin_required
def delete_map_story(filename):
    try:
        deleted = db_delete_card(filename)
        if not deleted:
            return jsonify({"success": False, "error": "Card não encontrado"})

        card_path = os.path.join(CARD_DIR, filename)
        if os.path.exists(card_path):
            os.remove(card_path)

        base_name = os.path.splitext(filename)[0]
        for f in os.listdir(TITLE_DIR):
            if os.path.splitext(f)[0] == base_name:
                os.remove(os.path.join(TITLE_DIR, f))

        return jsonify({"success": True, "card_name": base_name.capitalize()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# =========================== SALVAR ORDEM + VISIBILIDADE ===========================
@admin_bp.route("/admin/save_cards_order", methods=["POST"])
@admin_required
def save_cards_order():
    try:
        new_cards = request.get_json()
        if not isinstance(new_cards, list):
            return jsonify({"success": False, "error": "Formato inválido"})

        db_update_cards_order(new_cards)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ===========================
# Toggle "Novo!" do card
# ===========================
@admin_bp.route("/admin/toggle_card_new/<filename>", methods=["POST"])
@admin_required
def toggle_card_new(filename):
    data = request.get_json()
    is_new = data.get("is_new", False)
    new_since = datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat() if is_new else None
    db_update_card(filename, is_new=is_new, new_since=new_since)
    return jsonify({"success": True})


# =========================== SALVAR LINKS ===========================
@admin_bp.route("/admin/save_card_links/<filename>", methods=["POST"])
@admin_required
def save_card_links(filename):
    data = request.get_json()
    db_save_card_links(filename, data.get("historia", ""), data.get("mapa", ""))
    return jsonify({"success": True})

# =========================== LISTAR PARCEIROS ===========================

@admin_bp.route("/admin/list_partners", methods=["GET"])
@admin_required
def list_partners():
    partners = db_get_partners()
    return jsonify([
        {
            "nome": p.get("nome", ""),
            "file": p.get("file", "")
        }
        for p in partners
        if p.get("nome")
    ])

# =========================== ADICIONAR NOTÍCIA ===========================
@admin_bp.route("/admin/add_news", methods=["POST"])
@admin_required
def add_news():
    title = (request.form.get("title") or "").strip()
    subtitle = (request.form.get("subtitle") or "").strip()
    text = (request.form.get("text") or "").strip()

    btn_enabled = (request.form.get("btn_enabled") or "false").lower() == "true"
    btn_text = (request.form.get("btn_text") or "").strip()
    btn_type = (request.form.get("btn_type") or "url").strip()
    btn_target = (request.form.get("btn_target") or "").strip()

    btn_url = (request.form.get("btn_url") or "").strip()
    if not btn_target and btn_url:
        btn_target = btn_url
    if not btn_type:
        btn_type = "url"

    image = request.files.get("image")

    # -------- validações --------
    if not title:
        return jsonify({"success": False, "error": "Título é obrigatório."}), 400
    if not text:
        return jsonify({"success": False, "error": "Texto é obrigatório."}), 400
    if not image:
        return jsonify({"success": False, "error": "Imagem é obrigatória."}), 400

    if btn_enabled:
        if not btn_text or not btn_target:
            return jsonify({"success": False, "error": "Texto e destino do botão são obrigatórios quando o botão está ativado."}), 400

        if btn_type == "url":
            if not (btn_target.startswith("http://") or btn_target.startswith("https://") or btn_target.startswith("mailto:")):
                return jsonify({"success": False, "error": "Link do botão deve começar com http://, https:// ou mailto:"}), 400

        elif btn_type in ("partner", "card"):
            # aqui só exige que tenha destino
            # (se quiser, dá pra validar melhor depois)
            pass

        else:
            return jsonify({"success": False, "error": "Tipo de botão inválido."}), 400

    # -------- salvar imagem --------
    os.makedirs(NEWS_DIR, exist_ok=True)

    original_name = image.filename or ""
    safe_name = secure_filename(original_name)

    if not safe_name:
        return jsonify({"success": False, "error": "Nome de arquivo inválido."}), 400

    os.makedirs(NEWS_DIR, exist_ok=True)
    img_path = os.path.join(NEWS_DIR, safe_name)

    # não sobrescreve se já existir
    if os.path.exists(img_path):
        return jsonify({"success": False, "error": f"Já existe uma imagem com esse nome: {safe_name}. Renomeie o arquivo e tente novamente."}), 409

    image.save(img_path)

    item_id = db_insert_news(
        title=title,
        subtitle=subtitle,
        text=text,
        image=safe_name,
        button={"text": btn_text, "type": btn_type, "target": btn_target, "url": btn_target} if btn_enabled else None,
    )

    item = db_get_news_item(item_id)
    return jsonify({"success": True, "item": item})

# =========================== NOTÍCIAS: EDITAR ===========================

@admin_bp.route("/admin/list_news", methods=["GET"])
@admin_required
def list_news():
    news_list = db_list_news()

    def safe_item(n):
        return {
            "id": n.get("id"),
            "title": n.get("title", ""),
            "subtitle": n.get("subtitle", ""),
            "created_at": n.get("created_at", ""),
        }

    return jsonify([safe_item(n) for n in news_list])


@admin_bp.route("/admin/get_news/<int:news_id>", methods=["GET"])
@admin_required
def get_news(news_id: int):
    item = db_get_news_item(news_id)
    if not item:
        return jsonify({"success": False, "error": "Notícia não encontrada."}), 404

    return jsonify({"success": True, "item": item})


@admin_bp.route("/admin/update_news/<int:news_id>", methods=["POST"])
@admin_required
def update_news(news_id: int):
    title = (request.form.get("title") or "").strip()
    subtitle = (request.form.get("subtitle") or "").strip()
    text = (request.form.get("text") or "").strip()

    btn_enabled = (request.form.get("btn_enabled") or "false").lower() == "true"
    btn_text = (request.form.get("btn_text") or "").strip()

    btn_type = (request.form.get("btn_type") or "url").strip()
    btn_target = (request.form.get("btn_target") or "").strip()

    btn_url = (request.form.get("btn_url") or "").strip()
    if not btn_target and btn_url:
        btn_target = btn_url
    if not btn_type:
        btn_type = "url"

    new_image = request.files.get("image")  # opcional no editar

    if not title:
        return jsonify({"success": False, "error": "Título é obrigatório."}), 400
    if not text:
        return jsonify({"success": False, "error": "Texto é obrigatório."}), 400

    if btn_enabled:
        if not btn_text or not btn_target:
            return jsonify({"success": False, "error": "Texto e destino do botão são obrigatórios quando o botão está ativado."}), 400

        if btn_type == "url":
            if not (btn_target.startswith("http://") or btn_target.startswith("https://") or btn_target.startswith("mailto:")):
                return jsonify({"success": False, "error": "Link do botão deve começar com http://, https:// ou mailto:"}), 400

        elif btn_type in ("partner", "card"):
            pass
        else:
            return jsonify({"success": False, "error": "Tipo de botão inválido."}), 400

    item = db_get_news_item(news_id)
    if not item:
        return jsonify({"success": False, "error": "Notícia não encontrada."}), 404

    old_image_name = item.get("image", "")
    safe_name = old_image_name

    if new_image and (new_image.filename or ""):
        os.makedirs(NEWS_DIR, exist_ok=True)

        safe_name = secure_filename(new_image.filename)  # type: ignore
        if not safe_name:
            return jsonify({"success": False, "error": "Nome de arquivo inválido."}), 400

        new_path = os.path.join(NEWS_DIR, safe_name)

        if os.path.exists(new_path) and safe_name != old_image_name:
            return jsonify({"success": False, "error": f"Já existe uma imagem com esse nome: {safe_name}. Renomeie o arquivo e tente novamente."}), 409

        new_image.save(new_path)

        if old_image_name and old_image_name != safe_name:
            old_path = os.path.join(NEWS_DIR, old_image_name)
            if os.path.exists(old_path):
                os.remove(old_path)

    updated = db_update_news(
        news_id,
        title=title,
        subtitle=subtitle,
        text=text,
        image=safe_name,
        button={"text": btn_text, "type": btn_type, "target": btn_target, "url": btn_target} if btn_enabled else None,
    )

    if not updated:
        return jsonify({"success": False, "error": "Falha ao atualizar notícia."}), 500

    updated_item = db_get_news_item(news_id)
    return jsonify({"success": True, "item": updated_item})


@admin_bp.route("/admin/delete_news/<int:news_id>", methods=["DELETE"])
@admin_required
def delete_news(news_id: int):
    item = db_get_news_item(news_id)
    if not item:
        return jsonify({"success": False, "error": "Notícia não encontrada."}), 404

    deleted = db_delete_news(news_id)
    if not deleted:
        return jsonify({"success": False, "error": "Falha ao excluir notícia."}), 500

    img_name = item.get("image", "")
    if img_name:
        img_path = os.path.join(NEWS_DIR, img_name)
        if os.path.exists(img_path):
            os.remove(img_path)

    return jsonify({"success": True})
