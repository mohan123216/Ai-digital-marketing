"""app/services/media_upload.py

Supabase Storage helper for campaign ad media (images and videos).
"""
import mimetypes
import uuid
from pathlib import Path
from typing import Tuple

from app.services.supabase_client import get_supabase_admin_client
from config import settings

# ── Constants ────────────────────────────────────────────────────────────────
BUCKET = "campaign-ads-media"

ALLOWED_IMAGE_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/gif",
    "image/webp", "image/bmp",
}
ALLOWED_VIDEO_TYPES = {
    "video/mp4", "video/quicktime", "video/x-msvideo",
    "video/webm", "video/mpeg",
}
ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES

MAX_IMAGE_BYTES = 10 * 1024 * 1024   # 10 MB
MAX_VIDEO_BYTES = 200 * 1024 * 1024  # 200 MB


def _detect_content_type(filename: str, fallback: str) -> str:
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or fallback


def validate_media(filename: str, content_type: str, size_bytes: int) -> str:
    """Validate uploaded media. Returns the normalised content-type.
    Raises ValueError on failure.
    """
    ct = _detect_content_type(filename, content_type).lower()

    if ct not in ALLOWED_TYPES:
        raise ValueError(
            f"Unsupported file type '{ct}'. Allowed: JPG, PNG, GIF, WebP, MP4, MOV, AVI, WebM."
        )

    is_image = ct in ALLOWED_IMAGE_TYPES
    limit = MAX_IMAGE_BYTES if is_image else MAX_VIDEO_BYTES
    label = "10 MB" if is_image else "200 MB"

    if size_bytes > limit:
        raise ValueError(f"File too large. Max size for {'images' if is_image else 'videos'} is {label}.")

    return ct


def upload_ad_media(
    file_bytes: bytes,
    original_filename: str,
    content_type: str,
    user_id: str,
    campaign_run_id: str,
) -> Tuple[str, str]:
    """Upload bytes to Supabase Storage and return (public_url, storage_path).

    Parameters
    ----------
    file_bytes : bytes
    original_filename : str          e.g. "banner.png"
    content_type : str               MIME type
    user_id : str
    campaign_run_id : str

    Returns
    -------
    (public_url, storage_path)
    """
    ext = Path(original_filename).suffix.lower() or ".bin"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    storage_path = f"{user_id}/{campaign_run_id}/{unique_name}"

    db = get_supabase_admin_client()

    db.storage.from_(BUCKET).upload(
        path=storage_path,
        file=file_bytes,
        file_options={"content-type": content_type, "upsert": "true"},
    )

    public_url = db.storage.from_(BUCKET).get_public_url(storage_path)
    return public_url, storage_path
