from datetime import datetime
import pytz
import os
import re
import tempfile
import unicodedata
import hmac
from io import BytesIO
from flask import Blueprint, render_template, jsonify, request, current_app, redirect, url_for, session, send_file
from PIL import Image
from pypdf import PdfReader
from uuid import uuid4
from .register import promote_user, demote_user, delete_user
from tools.decorators import admin_required
from tools.uploads import is_safe_stored_filename, read_validated_image, save_internal_upload
from tools.db import (
    get_admin_count as db_get_admin_count,
    get_db as db_get_connection,
    get_all_users,
    get_cards as db_get_cards,
    get_card_by_file as db_get_card_by_file,
    get_story_by_card_file,
    get_story_pdf as db_get_story_pdf,
    save_story_pdf as db_save_story_pdf,
    delete_story_pdf as db_delete_story_pdf,
    save_story as db_save_story,
    undo_story_changes as db_undo_story_changes,
    get_partners as db_get_partners,
    get_card_links as db_get_card_links,
    get_site_status,
    get_site_visits,
    get_total_comments,
    get_latest_comment,
    insert_card as db_insert_card,
    delete_card as db_delete_card,
    update_cards_order as db_update_cards_order,
    update_card as db_update_card,
    save_card_links as db_save_card_links,
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
COVER_DIR = "static/images/covers/"
NEWS_DIR = "static/images/news/"
STORY_PDF_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "story_pdfs"))
CARD_IMAGE_FORMATS = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}


def _card_title_image_path(filename):
    base_name = os.path.splitext(filename)[0]
    for extension in (".png", ".jpg", ".jpeg", ".webp"):
        path = os.path.join(TITLE_DIR, f"{base_name}{extension}")
        if os.path.isfile(path):
            return path
    return None


def _card_image_version(path):
    try:
        return os.stat(path).st_mtime_ns
    except OSError:
        return 0


def _image_bytes_for_extension(image_content, extension):
    target_format = CARD_IMAGE_FORMATS.get(extension.lower())
    if not target_format:
        raise ValueError("O formato da imagem atual não pode ser substituído.")

    with Image.open(BytesIO(image_content)) as image:
        if image.format == target_format:
            return image_content
        if target_format == "JPEG":
            if image.mode in ("RGBA", "LA") or "transparency" in image.info:
                rgba_image = image.convert("RGBA")
                background = Image.new("RGB", rgba_image.size, "white")
                background.paste(rgba_image, mask=rgba_image.getchannel("A"))
                image = background
            else:
                image = image.convert("RGB")
        output = BytesIO()
        image.save(output, format=target_format, quality=92)
        return output.getvalue()


def _replace_card_images_and_update(filename, title_text, description, replacements):
    staged = []
    applied = []
    committed = False
    try:
        for target_path, content in replacements.items():
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            descriptor, staged_path = tempfile.mkstemp(prefix=".card-edit-", dir=os.path.dirname(target_path))
            with os.fdopen(descriptor, "wb") as staged_file:
                staged_file.write(content)
            staged.append((target_path, staged_path))

        for target_path, staged_path in staged:
            state = {"target": target_path, "backup": None, "original_moved": False, "installed": False}
            applied.append(state)
            if os.path.exists(target_path):
                descriptor, backup_path = tempfile.mkstemp(prefix=".card-edit-backup-", dir=os.path.dirname(target_path))
                os.close(descriptor)
                state["backup"] = backup_path
                os.replace(target_path, backup_path)
                state["original_moved"] = True
            os.replace(staged_path, target_path)
            state["installed"] = True

        updates = {}
        if title_text is not None:
            updates["title"] = title_text
        if description is not None:
            updates["description"] = description
        if updates and not db_update_card(filename, **updates):
            raise LookupError("Card não encontrado ou não atualizado.")
        committed = True
    except Exception:
        for state in reversed(applied):
            if state["installed"] and os.path.exists(state["target"]):
                os.remove(state["target"])
            if state["original_moved"] and state["backup"] and os.path.exists(state["backup"]):
                os.replace(state["backup"], state["target"])
        raise
    finally:
        for _, staged_path in staged:
            if os.path.exists(staged_path):
                os.remove(staged_path)
        if committed:
            for state in applied:
                if state["backup"] and os.path.exists(state["backup"]):
                    try:
                        os.remove(state["backup"])
                    except OSError:
                        current_app.logger.warning("Não foi possível remover backup temporário de imagem: %s", state["backup"])

# =========================== FUNÇÃO PARA CHECAR "NOVA" ===========================
def check_new_badges(cards):
    return db_check_new_badges(cards)


# =========================== ROTA PRINCIPAL ===========================
@admin_bp.route("/admin")
@admin_required
def admin():
    return render_template("admin.html")


@admin_bp.route("/admin_access/<token>", methods=["GET", "POST"])
def admin_access(token):
    if db_get_admin_count() > 0:
        return redirect(url_for("home.session_denied"))

    expected = current_app.config.get("BOOTSTRAP_ADMIN_TOKEN")
    used = current_app.config.get("BOOTSTRAP_ADMIN_TOKEN_USED", False)
    if not expected or used or not hmac.compare_digest(token, expected):
        return redirect(url_for("home.session_denied"))

    if request.method == "GET":
        return render_template("admin_access.html", token=token)

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
        card["link_mapa"] = card_links.get("mapa", "")
        pdf = db_get_story_pdf(file)
        card["pdf_filename"] = pdf.get("original_filename", "") if pdf else ""
        card["pdf_url"] = url_for("admin.view_story_pdf", filename=file) if pdf else ""

    return jsonify(cards)


def _read_validated_pdf(upload):
    name = getattr(upload, "filename", None) or ""
    if (
        not name
        or len(name) > 255
        or "/" in name
        or "\\" in name
        or "\x00" in name
        or any(ord(char) < 32 for char in name)
        or not name.lower().endswith(".pdf")
        or getattr(upload, "mimetype", "").lower() != "application/pdf"
    ):
        return None
    content = upload.stream.read(50 * 1024 * 1024 + 1)
    upload.stream.seek(0)
    if not content or len(content) > 50 * 1024 * 1024:
        return None
    try:
        pdf = PdfReader(BytesIO(content), strict=True)
        if pdf.is_encrypted or len(pdf.pages) == 0:
            return None
    except Exception:
        return None
    return name, content


def _stored_pdf_path(stored_filename):
    if not re.fullmatch(r"[a-f0-9]{32}\.pdf", stored_filename or ""):
        return None
    return os.path.join(STORY_PDF_DIR, stored_filename)


@admin_bp.route("/admin/upload_story_pdf/<filename>", methods=["POST"])
@admin_required
def upload_story_pdf(filename):
    card = next((card for card in db_get_cards() if card.get("file") == filename), None)
    if not card:
        return jsonify({"success": False, "error": "Card não encontrado."}), 404

    pdf_file = request.files.get("pdf_file")
    validated_pdf = _read_validated_pdf(pdf_file)
    if not validated_pdf:
        return jsonify({"success": False, "error": "Envie um arquivo PDF válido."}), 400

    original_name, pdf_content = validated_pdf
    stored_name = f"{uuid4().hex}.pdf"
    os.makedirs(STORY_PDF_DIR, exist_ok=True)
    stored_path = os.path.join(STORY_PDF_DIR, stored_name)
    try:
        with open(stored_path, "xb") as stored_file:
            stored_file.write(pdf_content)
        previous = db_save_story_pdf(filename, stored_name, original_name)
        if previous:
            previous_path = _stored_pdf_path(previous["stored_filename"])
            if previous_path and os.path.isfile(previous_path) and previous_path != stored_path:
                os.remove(previous_path)
        return jsonify({"success": True, "filename": original_name})
    except Exception:
        if os.path.isfile(stored_path):
            os.remove(stored_path)
        return jsonify({"success": False, "error": "Não foi possível salvar o PDF."}), 500


@admin_bp.route("/admin/delete_story_pdf/<filename>", methods=["DELETE"])
@admin_required
def delete_story_pdf(filename):
    pdf = db_delete_story_pdf(filename)
    if not pdf:
        return jsonify({"success": False, "error": "Arquivo não encontrado."}), 404
    stored_path = _stored_pdf_path(pdf["stored_filename"])
    if stored_path and os.path.isfile(stored_path):
        os.remove(stored_path)
    return jsonify({"success": True})


@admin_bp.route("/admin/story_pdf/<filename>")
@admin_required
def view_story_pdf(filename):
    pdf = db_get_story_pdf(filename)
    if not pdf:
        return redirect(url_for("home.session_denied"))
    stored_path = _stored_pdf_path(pdf["stored_filename"])
    if not stored_path or not os.path.isfile(stored_path):
        return redirect(url_for("home.session_denied"))
    return send_file(stored_path, mimetype="application/pdf", download_name=pdf["original_filename"], as_attachment=False)


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
    for card in cards:
        card["image_version"] = _card_image_version(os.path.join(CARD_DIR, card["file"]))
    return jsonify(cards)


@admin_bp.route("/admin/edit_card/<filename>", methods=["GET", "POST"])
@admin_required
def edit_card(filename):
    if not is_safe_stored_filename(filename):
        return jsonify({"success": False, "error": "Card inválido."}), 400

    card = db_get_card_by_file(filename)
    if not card:
        return jsonify({"success": False, "error": "Card não encontrado."}), 404

    card_path = os.path.join(CARD_DIR, filename)
    title_path = _card_title_image_path(filename)
    if request.method == "GET":
        return jsonify({
            "success": True,
            "file": card["file"],
            "title": card["title"],
            "description": card.get("description") or "",
            "card_image_url": url_for(
                "static", filename=f"images/cards/{filename}", v=_card_image_version(card_path)
            ),
            "title_image_url": url_for(
                "static",
                filename=f"images/titles/{os.path.basename(title_path)}",
                v=_card_image_version(title_path),
            ) if title_path else None,
        })

    title_text = request.form.get("title_text") if "title_text" in request.form else None
    description = request.form.get("description") if "description" in request.form else None
    if title_text is not None and (not isinstance(title_text, str) or not title_text.strip()):
        return jsonify({"success": False, "error": "O nome do Card não pode ficar vazio."}), 400
    if description is not None and not isinstance(description, str):
        return jsonify({"success": False, "error": "Informe a descrição do Card."}), 400

    replacements = {}
    card_upload = request.files.get("card_image")
    if card_upload and card_upload.filename:
        validated_card = read_validated_image(card_upload)
        if not validated_card:
            return jsonify({"success": False, "error": "Imagem do Card inválida ou acima de 10 MB."}), 400
        card_extension = os.path.splitext(filename)[1].lower()
        try:
            replacements[card_path] = _image_bytes_for_extension(validated_card[1], card_extension)
        except ValueError as error:
            return jsonify({"success": False, "error": str(error)}), 400

    title_upload = request.files.get("title_image")
    if title_upload and title_upload.filename:
        base_name = os.path.splitext(filename)[0]
        if any(
            other_card["file"] != filename
            and os.path.splitext(other_card["file"])[0] == base_name
            for other_card in db_get_cards()
        ):
            return jsonify({"success": False, "error": "A imagem do título é compartilhada com outro Card e não pode ser substituída com segurança."}), 409
        validated_title = read_validated_image(title_upload)
        if not validated_title:
            return jsonify({"success": False, "error": "Imagem do título inválida ou acima de 10 MB."}), 400
        title_extension = os.path.splitext(title_path)[1].lower() if title_path else validated_title[0]
        title_target = title_path or os.path.join(
            TITLE_DIR, f"{os.path.splitext(filename)[0]}{title_extension}"
        )
        shared_story_image = db_get_connection().execute(
            "SELECT 1 FROM stories WHERE hero_image = ? LIMIT 1",
            (os.path.basename(title_target),),
        ).fetchone()
        if shared_story_image:
            return jsonify({"success": False, "error": "A imagem do título também é usada por uma história e não pode ser substituída com segurança."}), 409
        try:
            replacements[title_target] = _image_bytes_for_extension(validated_title[1], title_extension)
        except ValueError as error:
            return jsonify({"success": False, "error": str(error)}), 400

    if title_text is None and description is None and not replacements:
        return jsonify({"success": False, "error": "Nenhuma alteração foi enviada."}), 400

    try:
        _replace_card_images_and_update(
            filename,
            title_text.strip() if title_text is not None else None,
            description,
            replacements,
        )
    except LookupError as error:
        return jsonify({"success": False, "error": str(error)}), 404
    except Exception:
        current_app.logger.exception("Falha ao editar Card")
        return jsonify({"success": False, "error": "Não foi possível salvar as alterações do Card."}), 500

    updated_card = db_get_card_by_file(filename)
    title_path = _card_title_image_path(filename)
    return jsonify({
        "success": True,
        "file": updated_card["file"],
        "title": updated_card["title"],
        "description": updated_card.get("description") or "",
        "card_image_url": url_for(
            "static", filename=f"images/cards/{filename}", v=_card_image_version(card_path)
        ),
        "title_image_url": url_for(
            "static",
            filename=f"images/titles/{os.path.basename(title_path)}",
            v=_card_image_version(title_path),
        ) if title_path else None,
    })


@admin_bp.route("/admin/overview_stats")
@admin_required
def overview_stats():
    users = get_all_users()
    latest_comment = get_latest_comment() or {}
    return jsonify({
        "online": get_site_status(),
        "site_visits": get_site_visits(),
        "total_users": len(users),
        "total_admins": db_get_admin_count(),
        "total_cards": len(db_get_cards()),
        "total_comments": get_total_comments(),
        "latest_comment": latest_comment,
    })


# =========================== ADICIONAR MAPA/HISTÓRIA ===========================
@admin_bp.route("/admin/add_map_story", methods=["POST"])
@admin_required
def add_map_story():
    description = request.form.get("description")
    title_text = request.form.get("title_text")
    card_image = request.files.get("card_image")

    if not description or not title_text or not card_image:
        return jsonify({"success": False, "error": "Faltando descrição, título ou imagem do card"})

    card_upload = read_validated_image(card_image)
    if not card_upload:
        return jsonify({"success": False, "error": "Imagem do card inválida ou acima de 10 MB."}), 400

    title_image = request.files.get("title_image")
    title_upload = read_validated_image(title_image) if title_image else None
    if title_image and not title_upload:
        return jsonify({"success": False, "error": "Imagem do título inválida ou acima de 10 MB."}), 400

    base_name = uuid4().hex
    card_filename = f"{base_name}{card_upload[0]}"
    created_paths = []
    try:
        save_internal_upload(CARD_DIR, card_filename, card_upload[1])
        created_paths.append(os.path.join(CARD_DIR, card_filename))
        if title_image:
            title_filename = f"{base_name}{title_upload[0]}"
            save_internal_upload(TITLE_DIR, title_filename, title_upload[1])
        else:
            title_filename = card_filename
            save_internal_upload(TITLE_DIR, title_filename, card_upload[1])
        created_paths.append(os.path.join(TITLE_DIR, title_filename))

        if not db_insert_card(card_filename, title_text, description):
            raise RuntimeError("A inserção do Card não foi confirmada.")
    except Exception:
        for path in created_paths:
            if os.path.isfile(path):
                os.remove(path)
        current_app.logger.exception("Falha ao criar Card")
        return jsonify({"success": False, "error": "Não foi possível criar o Card."}), 500
    return jsonify({"success": True})


# =========================== REMOVER MAPA/HISTÓRIA ===========================
@admin_bp.route("/admin/delete_map_story/<filename>", methods=["DELETE"])
@admin_required
def delete_map_story(filename):
    try:
        if request.headers.get("X-Card-Delete-Confirmed") != "true":
            return jsonify({"success": False, "error": "Confirme a remoção do Card."}), 400
        if not is_safe_stored_filename(filename):
            return jsonify({"success": False, "error": "Card inválido"}), 400

        # pegar story associado antes de remover o card para poder limpar arquivos (hero_image)
        story = get_story_by_card_file(filename)
        story_pdf = db_get_story_pdf(filename)

        deleted = db_delete_card(filename)
        if not deleted:
            return jsonify({"success": False, "error": "Card não encontrado"})

        # remover imagens do card e do título
        card_path = os.path.join(CARD_DIR, filename)
        if os.path.exists(card_path):
            os.remove(card_path)

        base_name = os.path.splitext(filename)[0]
        for f in os.listdir(TITLE_DIR):
            if os.path.splitext(f)[0] == base_name:
                try:
                    os.remove(os.path.join(TITLE_DIR, f))
                except Exception:
                    pass

        # remover imagem de capa/hero da história, se existir
        if story and story.get("hero_image"):
            hero_file = story.get("hero_image")
            hero_path = os.path.join(COVER_DIR, hero_file) if is_safe_stored_filename(hero_file) else None
            if hero_path and os.path.exists(hero_path):
                try:
                    os.remove(hero_path)
                except Exception:
                    pass

        if story_pdf:
            pdf_path = os.path.join(STORY_PDF_DIR, story_pdf["stored_filename"])
            if os.path.isfile(pdf_path):
                try:
                    os.remove(pdf_path)
                except Exception:
                    pass

        return jsonify({"success": True, "card_name": base_name.capitalize()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# =========================== SALVAR ORDEM + VISIBILIDADE ===========================
@admin_bp.route("/admin/save_cards_order", methods=["POST"])
@admin_required
def save_cards_order():
    try:
        new_cards = request.get_json(silent=True)
        if not isinstance(new_cards, list):
            return jsonify({"success": False, "error": "Formato inválido"}), 400

        db_update_cards_order(new_cards)
        return jsonify({"success": True})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        current_app.logger.exception("Falha ao salvar ordem dos Cards")
        return jsonify({"success": False, "error": "Não foi possível salvar a ordem dos Cards."}), 500

# ===========================
# Toggle "Novo!" do card
# ===========================
@admin_bp.route("/admin/toggle_card_new/<filename>", methods=["POST"])
@admin_required
def toggle_card_new(filename):
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or type(data.get("is_new")) is not bool:
        return jsonify({"success": False, "error": "Formato inválido."}), 400
    is_new = data["is_new"]
    new_since = datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat() if is_new else None
    if not db_update_card(filename, is_new=is_new, new_since=new_since):
        return jsonify({"success": False, "error": "Card não encontrado."}), 404
    return jsonify({"success": True})


# =========================== SALVAR LINKS ===========================
@admin_bp.route("/admin/save_card_links/<filename>", methods=["POST"])
@admin_required
def save_card_links(filename):
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("mapa", ""), str):
        return jsonify({"success": False, "error": "Formato inválido."}), 400
    try:
        if not db_save_card_links(filename, data.get("mapa", "")):
            return jsonify({"success": False, "error": "Card não encontrado."}), 404
    except Exception:
        current_app.logger.exception("Falha ao salvar link do Card")
        return jsonify({"success": False, "error": "Não foi possível salvar o link."}), 500
    return jsonify({"success": True})


@admin_bp.route("/admin/get_story/<filename>")
@admin_required
def get_story(filename):
    story = get_story_by_card_file(filename)
    if not story:
        return jsonify({"exists": False})
    editor_content = story.get("draft_content") if story.get("draft_content") is not None else story.get("content", "")
    return jsonify({
        "exists": True,
        "slug": story.get("slug"),
        "content": editor_content,
        "hero_image": story.get("hero_image", ""),
        "draft_content": story.get("draft_content"),
        "published_content": story.get("published_content") or story.get("content", ""),
        "status": story.get("status", "published"),
        "scheduled_at": story.get("scheduled_at"),
    })


@admin_bp.route("/admin/save_story/<filename>", methods=["POST"])
@admin_required
def save_story(filename):
    if request.is_json:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"success": False, "error": "Formato inválido."}), 400
        content = data.get("content")
        action = data.get("action", "publish")
        scheduled_at = data.get("scheduled_at", "")
    else:
        content = request.form.get("content")
        action = request.form.get("action", "publish")
        scheduled_at = request.form.get("scheduled_at", "")

    if not isinstance(content, str) or not content.strip():
        return jsonify({"success": False, "error": "Conteúdo da história não pode ficar vazio."}), 400
    if not isinstance(action, str) or action not in {"draft", "scheduled", "publish"}:
        return jsonify({"success": False, "error": "Ação da história inválida."}), 400
    if not isinstance(scheduled_at, str):
        return jsonify({"success": False, "error": "Data de publicação inválida."}), 400
    if action == "scheduled":
        try:
            datetime.fromisoformat(scheduled_at)
        except ValueError:
            return jsonify({"success": False, "error": "Data de publicação inválida."}), 400

    card = next((c for c in db_get_cards() if c["file"] == filename), None)
    if not card:
        return jsonify({"success": False, "error": "Card não encontrado."}), 404

    def slugify(text):
        normalized = unicodedata.normalize("NFKD", text)
        normalized = normalized.encode("ascii", "ignore").decode("ascii")
        normalized = normalized.lower()
        normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
        normalized = normalized.strip("-")
        return normalized

    existing_story = get_story_by_card_file(filename)
    slug = existing_story.get("slug") if existing_story and existing_story.get("slug") else slugify(card.get("title", ""))
    hero_image = None
    new_hero_path = None
    hero_file = request.files.get("hero_image")
    if hero_file:
        hero_upload = read_validated_image(hero_file)
        if not hero_upload:
            return jsonify({"success": False, "error": "Imagem de capa inválida ou acima de 10 MB."}), 400
        os.makedirs(COVER_DIR, exist_ok=True)
        hero_filename = f"{uuid4().hex}{hero_upload[0]}"
        save_internal_upload(COVER_DIR, hero_filename, hero_upload[1])
        new_hero_path = os.path.join(COVER_DIR, hero_filename)
        hero_image = hero_filename
    elif existing_story and existing_story.get("hero_image"):
        hero_image = existing_story.get("hero_image")

    try:
        if not db_save_story(filename, slug, content, hero_image, action=action, scheduled_at=scheduled_at or None):
            raise RuntimeError("A gravação da história não foi confirmada.")
    except ValueError as e:
        if new_hero_path and os.path.isfile(new_hero_path):
            os.remove(new_hero_path)
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception:
        if new_hero_path and os.path.isfile(new_hero_path):
            os.remove(new_hero_path)
        current_app.logger.exception("Falha ao salvar história")
        return jsonify({"success": False, "error": "Não foi possível salvar a história."}), 500
    return jsonify({"success": True, "slug": slug, "status": action if action in {"draft", "scheduled"} else "published"})


@admin_bp.route("/admin/undo_story/<filename>", methods=["POST"])
@admin_required
def undo_story(filename):
    if db_undo_story_changes(filename):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Não foi possível desfazer as alterações."}), 400


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

    validated_image = read_validated_image(image)
    if not validated_image:
        return jsonify({"success": False, "error": "Imagem inválida ou acima de 10 MB."}), 400
    safe_name = f"{uuid4().hex}{validated_image[0]}"
    save_internal_upload(NEWS_DIR, safe_name, validated_image[1])

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
        validated_image = read_validated_image(new_image)
        if not validated_image:
            return jsonify({"success": False, "error": "Imagem inválida ou acima de 10 MB."}), 400

        safe_name = f"{uuid4().hex}{validated_image[0]}"
        save_internal_upload(NEWS_DIR, safe_name, validated_image[1])

        if old_image_name and old_image_name != safe_name:
            old_path = os.path.join(NEWS_DIR, old_image_name) if is_safe_stored_filename(old_image_name) else None
            if old_path and os.path.exists(old_path):
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
        img_path = os.path.join(NEWS_DIR, img_name) if is_safe_stored_filename(img_name) else None
        if img_path and os.path.exists(img_path):
            os.remove(img_path)

    return jsonify({"success": True})
