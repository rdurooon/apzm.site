from datetime import datetime, timedelta
import os
import json
import shutil
from flask import Blueprint, render_template, jsonify, request
from werkzeug.utils import secure_filename
from .register import load_users, promote_user, demote_user, delete_user
from tools.decorators import admin_required

admin_bp = Blueprint("admin", __name__)

# =========================== CONSTANTES ===========================
DATA_FILE = "data/cards.json"
LINKS_FILE = "data/links.json"
CARD_DIR = "static/images/cards/"
TITLE_DIR = "static/images/titles/"


# =========================== FUNÇÕES AUXILIARES ===========================
def read_json(path, default=None):
    """Lê JSON de um arquivo, retornando default em caso de erro."""
    if not os.path.exists(path):
        return default if default is not None else []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default if default is not None else []


def write_json(path, data):
    """Salva JSON no arquivo com indentação e UTF-8."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# =========================== FUNÇÃO PARA CHECAR "NOVA" ===========================
def check_new_badges(cards):
    now = datetime.utcnow()
    changed = False
    for card in cards:
        if card.get("is_new") and card.get("new_since"):
            try:
                new_since = datetime.fromisoformat(card["new_since"])
                if now - new_since > timedelta(days=7):
                    card["is_new"] = False
                    card["new_since"] = None
                    changed = True
            except Exception:
                card["new_since"] = None
    if changed:
        write_json(DATA_FILE, cards)
    return cards


# =========================== ROTA PRINCIPAL ===========================
@admin_bp.route("/admin")
@admin_required
def admin():
    return render_template("admin.html")


# =========================== LISTAR USUÁRIOS ===========================
@admin_bp.route("/admin/list_users")
def list_users():
    users = load_users()
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
    cards = read_json(DATA_FILE, [])
    links_data = read_json(LINKS_FILE, {})

    for card in cards:
        file = card["file"]
        card_links = links_data.get(file, {}) # type: ignore
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
    cards = read_json(DATA_FILE, [])
    # Atualiza status de "Novo!" baseado em new_since
    cards = check_new_badges(cards)
    return jsonify(cards)


# =========================== ADICIONAR MAPA/HISTÓRIA ===========================
@admin_bp.route("/admin/add_map_story", methods=["POST"])
@admin_required
def add_map_story():
    description = request.form.get("description")
    card_image = request.files.get("card_image")

    if not description or not card_image:
        return jsonify({"success": False, "error": "Faltando descrição ou imagem do card"})

    # Salva imagem do card
    card_filename = secure_filename(card_image.filename) # type: ignore
    card_path = os.path.join(CARD_DIR, card_filename)
    card_image.save(card_path)

    # Salva imagem do título (ou usa o mesmo arquivo do card)
    title_image = request.files.get("title_image")
    if title_image:
        title_filename = secure_filename(title_image.filename) # type: ignore
        title_path = os.path.join(TITLE_DIR, title_filename)
        title_image.save(title_path)
    else:
        title_filename = card_filename
        title_path = os.path.join(TITLE_DIR, title_filename)
        shutil.copy(card_path, title_path)

    # Atualiza JSON
    cards = read_json(DATA_FILE, [])
    title_json = os.path.splitext(card_filename)[0].capitalize()

    cards.append({
        "file": card_filename,
        "title": title_json,
        "description": description
    })

    write_json(DATA_FILE, cards)
    return jsonify({"success": True})


# =========================== REMOVER MAPA/HISTÓRIA ===========================
@admin_bp.route("/admin/delete_map_story/<filename>", methods=["DELETE"])
@admin_required
def delete_map_story(filename):
    try:
        cards = read_json(DATA_FILE, [])
        card_to_delete = next((c for c in cards if c["file"] == filename), None)

        if not card_to_delete:
            return jsonify({"success": False, "error": "Card não encontrado"})

        # Remove do JSON
        cards = [c for c in cards if c["file"] != filename]
        write_json(DATA_FILE, cards)

        # Remove imagem do card
        card_path = os.path.join(CARD_DIR, filename)
        if os.path.exists(card_path):
            os.remove(card_path)

        # Remove imagem do título
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

        current_cards = read_json(DATA_FILE, [])
        cards_dict = {c["file"]: c for c in current_cards}

        updated_cards = [
            {
                "file": c.get("file"),
                "title": cards_dict.get(c.get("file"), {}).get("title", os.path.splitext(c.get("file"))[0].capitalize()),
                "description": cards_dict.get(c.get("file"), {}).get("description", ""),
                "visible": c.get("visible", True),
            }
            for c in new_cards if c.get("file")
        ]

        write_json(DATA_FILE, updated_cards)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ===========================
# Toggle "Novo!" do card
# ===========================
@admin_bp.route("/admin/toggle_card_new/<filename>", methods=["POST"])
@admin_required
def toggle_card_new(filename):
    cards = read_json(DATA_FILE, [])
    data = request.get_json()
    is_new = data.get("is_new", False)

    for card in cards:
        if card["file"] == filename:
            card["is_new"] = is_new
            if is_new:
                card["new_since"] = datetime.utcnow().isoformat()
            else:
                card["new_since"] = None
            break

    write_json(DATA_FILE, cards)
    return jsonify({"success": True})


# =========================== SALVAR LINKS ===========================
@admin_bp.route("/admin/save_card_links/<filename>", methods=["POST"])
@admin_required
def save_card_links(filename):
    data = request.get_json()
    links_data = read_json(LINKS_FILE, {})

    links_data[filename] = {
        "historia": data.get("historia", ""),
        "mapa": data.get("mapa", "")
    }

    write_json(LINKS_FILE, links_data)
    return jsonify({"success": True})
