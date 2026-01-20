from datetime import datetime, timedelta
import pytz
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
PARTNERS_FILE = "data/parceiros.json"
NEWS_FILE = "data/news.json"
NEWS_DIR = "static/images/news/"

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
    now = datetime.now(pytz.timezone("America/Sao_Paulo"))
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
@admin_required
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
    title_text = request.form.get("title_text")
    card_image = request.files.get("card_image")

    if not description or not title_text or not card_image:
        return jsonify({"success": False, "error": "Faltando descrição, título ou imagem do card"})

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

    cards.append({
        "file": card_filename,
        "title": title_text,
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
                card["new_since"] = datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat()
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

# =========================== LISTAR PARCEIROS ===========================

@admin_bp.route("/admin/list_partners", methods=["GET"])
@admin_required
def list_partners():
    partners = read_json(PARTNERS_FILE, [])
    if not isinstance(partners, list):
        partners = []

    # retorna só o necessário
    return jsonify([
        {
            "nome": p.get("nome", ""),
            "file": p.get("file", "")  # se você usa file/id no front
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
            if not (btn_target.startswith("http://") or btn_target.startswith("https://")):
                return jsonify({"success": False, "error": "Link do botão deve começar com http:// ou https://"}), 400

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

    img_path = os.path.join(NEWS_DIR, safe_name)

    # não sobrescreve se já existir
    if os.path.exists(img_path):
        return jsonify({"success": False, "error": f"Já existe uma imagem com esse nome: {safe_name}. Renomeie o arquivo e tente novamente."}), 409

    image.save(img_path)

    # -------- atualizar news.json --------
    news_list = read_json(NEWS_FILE, [])
    if not isinstance(news_list, list):
        news_list = []

    created_at = datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat()

    item = {
        "id": int(datetime.now().timestamp() * 1000),
        "title": title,
        "subtitle": subtitle,
        "text": text,
        "image": safe_name,      # só o nome do arquivo
        "created_at": created_at
    }

    if btn_enabled:
        # mantém compat com front antigo e deixa o novo completo
        button_obj = {"text": btn_text, "type": btn_type, "target": btn_target}
        if btn_type == "url":
            button_obj["url"] = btn_target  # compat: quem ainda lê "url" continua funcionando
        item["button"] = button_obj
    else:
        item["button"] = None


    # mais recente primeiro
    news_list.insert(0, item)
    write_json(NEWS_FILE, news_list)

    return jsonify({"success": True, "item": item})

# =========================== NOTÍCIAS: EDITAR ===========================

@admin_bp.route("/admin/list_news", methods=["GET"])
@admin_required
def list_news():
    news_list = read_json(NEWS_FILE, [])
    if not isinstance(news_list, list):
        news_list = []

    # retorna só o necessário para a “lista de edição”
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
    news_list = read_json(NEWS_FILE, [])
    if not isinstance(news_list, list):
        news_list = []

    item = next((n for n in news_list if int(n.get("id", -1)) == news_id), None)
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
            if not (btn_target.startswith("http://") or btn_target.startswith("https://")):
                return jsonify({"success": False, "error": "Link do botão deve começar com http:// ou https://"}), 400

        elif btn_type in ("partner", "card"):
            pass
        else:
            return jsonify({"success": False, "error": "Tipo de botão inválido."}), 400

    news_list = read_json(NEWS_FILE, [])
    if not isinstance(news_list, list):
        news_list = []

    idx = next((i for i, n in enumerate(news_list) if int(n.get("id", -1)) == news_id), None)
    if idx is None:
        return jsonify({"success": False, "error": "Notícia não encontrada."}), 404

    item = news_list[idx]
    old_image_name = item.get("image", "")

    # -------- troca de imagem (se enviou uma nova) --------
    if new_image and (new_image.filename or ""):
        os.makedirs(NEWS_DIR, exist_ok=True)

        safe_name = secure_filename(new_image.filename)  # type: ignore
        if not safe_name:
            return jsonify({"success": False, "error": "Nome de arquivo inválido."}), 400

        new_path = os.path.join(NEWS_DIR, safe_name)

        # Se já existe um arquivo com esse nome e ele não é o mesmo da notícia atual, bloqueia (evita sobrescrever outro)
        if os.path.exists(new_path) and safe_name != old_image_name:
            return jsonify({"success": False, "error": f"Já existe uma imagem com esse nome: {safe_name}. Renomeie o arquivo e tente novamente."}), 409

        # salva nova
        new_image.save(new_path)

        # apaga antiga se for diferente
        if old_image_name and old_image_name != safe_name:
            old_path = os.path.join(NEWS_DIR, old_image_name)
            if os.path.exists(old_path):
                os.remove(old_path)

        item["image"] = safe_name

    # -------- atualiza campos --------
    item["title"] = title
    item["subtitle"] = subtitle
    item["text"] = text
    item["button"] = (
        {"text": btn_text, "type": btn_type, "target": btn_target, **({"url": btn_target} if btn_type == "url" else {})}
        if btn_enabled else None
    )


    news_list[idx] = item
    write_json(NEWS_FILE, news_list)

    return jsonify({"success": True, "item": item})


@admin_bp.route("/admin/delete_news/<int:news_id>", methods=["DELETE"])
@admin_required
def delete_news(news_id: int):
    news_list = read_json(NEWS_FILE, [])
    if not isinstance(news_list, list):
        news_list = []

    item = next((n for n in news_list if int(n.get("id", -1)) == news_id), None)
    if not item:
        return jsonify({"success": False, "error": "Notícia não encontrada."}), 404

    # remove do json
    news_list = [n for n in news_list if int(n.get("id", -1)) != news_id]
    write_json(NEWS_FILE, news_list)

    # remove imagem
    img_name = item.get("image", "")
    if img_name:
        img_path = os.path.join(NEWS_DIR, img_name)
        if os.path.exists(img_path):
            os.remove(img_path)

    return jsonify({"success": True})
