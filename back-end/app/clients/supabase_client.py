from config import settings
from supabase import Client, create_client


def get_supabase_client() -> Client:
    """Initialize and return the raw Supabase connection.

    Returns:
        A Supabase client instance bound to the configured project.
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
