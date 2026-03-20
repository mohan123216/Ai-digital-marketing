from typing import Any, Dict, Optional

from app.services.supabase_client import get_supabase_admin_client
from config import settings


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    client = get_supabase_admin_client()
    response = (
        client.table(settings.SUPABASE_USERS_TABLE)
        .select("id,email,password_hash,created_at")
        .eq("email", email)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    client = get_supabase_admin_client()
    response = (
        client.table(settings.SUPABASE_USERS_TABLE)
        .select("id,email,created_at")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def create_user(email: str, password_hash: str) -> Dict[str, Any]:
    client = get_supabase_admin_client()
    (
        client.table(settings.SUPABASE_USERS_TABLE)
        .insert({"email": email, "password_hash": password_hash})
        .execute()
    )
    created_user = get_user_by_email(email)
    if not created_user or not created_user.get("id"):
        raise RuntimeError("User created but could not fetch generated id")
    return created_user
