from functools import lru_cache
from supabase import Client, create_client

from config import settings


@lru_cache
def get_supabase_admin_client() -> Client:
    """
    Create and cache a Supabase admin client.
    Uses service role key so backend can securely read/write per-user workflow data.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
        )
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
