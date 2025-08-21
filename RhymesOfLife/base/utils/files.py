import math
import os
from typing import Optional, Tuple, Set

import magic
from PIL import Image, UnidentifiedImageError
from PIL.Image import DecompressionBombError


def _reset(f) -> None:
    if hasattr(f, "seek"):
        try:
            f.seek(0)
        except Exception:
            pass


def _safe_mime_from_buffer(buf: bytes) -> Optional[str]:
    try:
        return magic.from_buffer(buf, mime=True)
    except Exception:
        return None


def _mb(n: int) -> int:
    return math.ceil(n / (1024 * 1024))


def validate_image_upload(
    uploaded_file,
    *,
    max_size_bytes: Optional[int] = None,
    max_side_px: Optional[int] = None,
    allowed_mimes: Optional[Set[str]] = None,
    allowed_formats: Optional[Set[str]] = None,
    max_total_pixels: Optional[int] = 100_000_000,
) -> Tuple[bool, Optional[str]]:
    name = getattr(uploaded_file, "name", "file")

    size = getattr(uploaded_file, "size", None)
    if max_size_bytes and size and size > max_size_bytes:
        return False, f"File exceeds {_mb(max_size_bytes)}MB: {name}"

    if allowed_mimes is not None:
        head = uploaded_file.read(1024)
        _reset(uploaded_file)
        mime = _safe_mime_from_buffer(head)
        if not mime or mime not in allowed_mimes:
            return False, f"Invalid MIME type: {mime or 'unknown'}"

    try:
        pos = uploaded_file.tell() if hasattr(uploaded_file, "tell") else None
        img = Image.open(uploaded_file)
        img.verify()
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(0 if pos is None else pos)

        img = Image.open(uploaded_file)
        w, h = img.size

        if max_side_px and (w > max_side_px or h > max_side_px):
            return False, f"Image is too large (max {max_side_px}px per side): {name}"

        if max_total_pixels and (w * h) > max_total_pixels:
            return False, "Image has too many pixels."

        fmt = (img.format or "").strip().upper()
        if allowed_formats is not None and fmt not in {f.strip().upper() for f in allowed_formats}:
            return False, f"Image format {fmt or 'unknown'} is not supported."
    except DecompressionBombError:
        return False, "Image is too large or suspicious (decompression bomb)."
    except UnidentifiedImageError:
        return False, "The uploaded file is not a valid image."
    except Exception:
        return False, f"Problem with image file: {name}"
    finally:
        _reset(uploaded_file)

    return True, None


def validate_mixed_upload(
    uploaded_file,
    *,
    allowed_exts: Set[str],
    allowed_mimes: Set[str],
    max_size_bytes: int,
    max_image_side_px: int,
) -> Tuple[bool, Optional[str]]:
    name = getattr(uploaded_file, "name", "file")
    ext = os.path.splitext(name)[1].lower()
    if ext not in allowed_exts:
        return False, f"Invalid extension: {name}"

    size = getattr(uploaded_file, "size", None)
    if size and size > max_size_bytes:
        return False, f"File exceeds {_mb(max_size_bytes)}MB: {name}"

    head = uploaded_file.read(1024)
    _reset(uploaded_file)
    mime = _safe_mime_from_buffer(head)
    if not mime or mime not in allowed_mimes:
        return False, f"Invalid MIME type: {mime or 'unknown'}"

    if mime.startswith("image/"):
        ok, err = validate_image_upload(
            uploaded_file,
            max_size_bytes=max_size_bytes,
            max_side_px=max_image_side_px,
            allowed_mimes=None,
            allowed_formats=None,
        )
        if not ok:
            return False, err

    return True, None
