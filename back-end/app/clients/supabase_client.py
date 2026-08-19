from config import Settings, get_settings
from supabase import Client, create_client


def get_supabase_client(settings: Settings | None = None) -> Client:
    """Initialize and return the raw Supabase connection.

    Args:
        settings: Optional pre-built settings; defaults to the cached
            application settings.

    Returns:
        A Supabase client instance bound to the configured project.
    """
    settings = settings or get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
