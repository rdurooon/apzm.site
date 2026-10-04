import os
import re
from io import BytesIO

from PIL import Image, UnidentifiedImageError


MAX_IMAGE_UPLOAD_BYTES = 10 * 1024 * 1024
_IMAGE_FORMATS = {
    ".jpg": ("JPEG", "image/jpeg"),
    ".jpeg": ("JPEG", "image/jpeg"),
    ".png": ("PNG", "image/png"),
    ".webp": ("WEBP", "image/webp"),
}


def read_validated_image(upload, max_bytes=MAX_IMAGE_UPLOAD_BYTES):
    filename = getattr(upload, "filename", None) or ""
    if not filename or any(char in filename for char in ("/", "\\", "\x00")):
        return None

    extension = os.path.splitext(filename)[1].lower()
    expected_format = _IMAGE_FORMATS.get(extension)
    if not expected_format or getattr(upload, "mimetype", "").lower() != expected_format[1]:
        return None

    content = upload.stream.read(max_bytes + 1)
    upload.stream.seek(0)
    if not content or len(content) > max_bytes:
        return None

    try:
        with Image.open(BytesIO(content)) as image:
            if image.format != expected_format[0] or image.width * image.height > 25_000_000:
                return None
            image.verify()
        with Image.open(BytesIO(content)) as image:
            image.load()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        return None

    return extension, content


def save_internal_upload(directory, filename, content):
    if not re.fullmatch(r"[a-f0-9]{32}\.(?:jpg|jpeg|png|webp)", filename or ""):
        raise ValueError("Nome interno de upload inválido.")

    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, "xb") as uploaded_file:
        uploaded_file.write(content)
    return path


def is_safe_stored_filename(filename):
    return bool(
        filename
        and len(filename) <= 255
        and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", filename)
    )