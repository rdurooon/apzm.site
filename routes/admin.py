import os
import json
from flask import Blueprint, render_template, url_for, jsonify, request
from werkzeug.utils import secure_filename
from .register import load_users, promote_user, demote_user, delete_user  # Funções de manipulação
from tools.decorators import admin_required

admin_bp = Blueprint("admin", __name__)

# =========================== PASTAS E ARQUIVOS ===========================
DATA_FILE = 'data/cards.json'
CARD_DIR = 'static/images/cards/'
TITLE_DIR = 'static/images/titles/'

# =========================== ROTA PRINCIPAL ===========================
@admin_bp.route("/admin")
@admin_required
def admin():
    return render_template('admin.html')

# ======================= ROTAS AUXILIARES =========================
@admin_bp.route("/admin/list_users")
def list_users():
    users = load_users()
    users_list = []
    for u in users:
        users_list.append({
            "id": u["id"],
            "username": u["username"],
            "is_admin": u.get("is_admin", False),  # Adiciona status de admin
            "created_at": u.get("created_at", "Desconhecido")
        })
    return jsonify(users_list)

# =========================== PROMOVER USUÁRIO ===========================
@admin_bp.route("/admin/promote/<user_id>", methods=['POST'])
@admin_required
def promote(user_id):
    success = promote_user(user_id)  # Implementar na register.py
    return jsonify({"success": success})

# =========================== REMOVER ADMIN ===========================
@admin_bp.route("/admin/demote/<user_id>", methods=['POST'])
@admin_required
def demote(user_id):
    success = demote_user(user_id)
    return jsonify({"success": success})

# =========================== DELETAR USUÁRIO ===========================
@admin_bp.route("/admin/delete/<user_id>", methods=['DELETE'])
@admin_required
def delete(user_id):
    success = delete_user(user_id)
    return jsonify({"success": success})

# =========================== LISTAR CARDS ===========================
@admin_bp.route("/admin/list_cards")
@admin_required
def list_cards():
    if not os.path.exists(DATA_FILE):
        return jsonify([])
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            cards = json.load(f)
    except:
        cards = []
    return jsonify(cards)

# =========================== ADICIONAR MAPA/HISTÓRIA ===========================
@admin_bp.route("/admin/add_map_story", methods=['POST'])
@admin_required
def add_map_story():
    description = request.form.get('description')
    card_image = request.files.get('card_image')

    # Verifica se os dados mínimos foram enviados
    if not description or not card_image:
        return jsonify({'success': False, 'error': 'Faltando descrição ou imagem do card'})

    # =========================== SALVA IMAGEM DO CARD ===========================
    card_filename = secure_filename(card_image.filename)
    card_path = os.path.join(CARD_DIR, card_filename)
    card_image.save(card_path)

# =========================== SALVA IMAGEM DO TÍTULO ===========================
    title_image = request.files.get('title_image')
    if title_image:
        title_filename = secure_filename(title_image.filename)
        title_path = os.path.join(TITLE_DIR, title_filename)
        title_image.save(title_path)
    else:
        # fallback: usa o mesmo arquivo do card
        title_filename = card_filename
        title_path = os.path.join(TITLE_DIR, title_filename)
        # copia a imagem do card para a pasta de títulos
        import shutil
        shutil.copy(card_path, title_path)


    # =========================== ATUALIZA JSON ===========================
    if not os.path.exists(DATA_FILE):
        cards = []
    else:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                cards = json.load(f)
            except:
                cards = []

    # Gera título do JSON a partir do nome do arquivo, primeira letra maiúscula
    title_json = os.path.splitext(card_filename)[0].capitalize()

    # Adiciona novo mapa/história
    cards.append({
        "file": card_filename,
        "title": title_json,
        "description": description
    })

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(cards, f, ensure_ascii=False, indent=4)

    return jsonify({'success': True})

# =========================== REMOVER MAPA/HISTÓRIA ===========================
@admin_bp.route("/admin/delete_map_story/<filename>", methods=['DELETE'])
@admin_required
def delete_map_story(filename):
    try:
        # Carrega JSON
        if not os.path.exists(DATA_FILE):
            return jsonify({'success': False, 'error': 'Arquivo cards.json não encontrado'})

        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            cards = json.load(f)

        # Encontra o card pelo nome do arquivo
        card_to_delete = next((c for c in cards if c["file"] == filename), None)
        if not card_to_delete:
            return jsonify({'success': False, 'error': 'Card não encontrado'})

        # Remove do JSON
        cards = [c for c in cards if c["file"] != filename]
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(cards, f, ensure_ascii=False, indent=4)

        # Remove imagem do card
        card_path = os.path.join(CARD_DIR, filename)
        if os.path.exists(card_path):
            os.remove(card_path)

        # Remove imagem do título: busca qualquer arquivo que comece com o mesmo nome do card
        base_name = os.path.splitext(filename)[0]  # "cathedral.jpg" -> "cathedral"
        for f in os.listdir(TITLE_DIR):
            if os.path.splitext(f)[0] == base_name:
                os.remove(os.path.join(TITLE_DIR, f))

        # Retorna sucesso com o nome formatado para o popup
        card_name_formatted = base_name.capitalize()
        return jsonify({'success': True, 'card_name': card_name_formatted})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
