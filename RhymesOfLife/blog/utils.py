import os
from typing import Optional, Tuple

import magic
from PIL import Image, UnidentifiedImageError
from PIL.Image import DecompressionBombError


def _reset(f) -> None:
    if hasattr(f, "seek"):
        try:
            f.seek(0)
        except Exception:
            pass


def validate_image_upload(
    uploaded_file,
    *,
    max_size_bytes: Optional[int] = None,
    max_side_px: Optional[int] = None,
    allowed_mimes: Optional[set] = None,
    allowed_formats: Optional[set] = None,
) -> Tuple[bool, Optional[str]]:

    name = getattr(uploaded_file, "name", "file")

    if max_size_bytes and getattr(uploaded_file, "size", None) and uploaded_file.size > max_size_bytes:
        return False, f"File exceeds {max_size_bytes // (1024 * 1024)}MB: {name}"

    if allowed_mimes is not None:
        head = uploaded_file.read(1024)
        _reset(uploaded_file)
        mime = magic.from_buffer(head, mime=True)
        if mime not in allowed_mimes:
            return False, f"Invalid MIME type: {mime}"

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

        fmt = (img.format or "").upper()
        if allowed_formats is not None and fmt not in allowed_formats:
            return False, f"Image format {fmt} is not supported."
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
    allowed_exts: set,
    allowed_mimes: set,
    max_size_bytes: int,
    max_image_side_px: int,
) -> Tuple[bool, Optional[str]]:

    name = getattr(uploaded_file, "name", "file")
    ext = os.path.splitext(name)[1].lower()
    if ext not in allowed_exts:
        return False, f"Invalid extension: {name}"

    if getattr(uploaded_file, "size", None) and uploaded_file.size > max_size_bytes:
        return False, f"File exceeds {max_size_bytes // (1024 * 1024)}MB: {name}"

    head = uploaded_file.read(1024)
    _reset(uploaded_file)
    mime = magic.from_buffer(head, mime=True)
    if mime not in allowed_mimes:
        return False, f"Invalid MIME type: {mime}"

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
