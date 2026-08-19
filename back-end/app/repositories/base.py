from app.clients.supabase_client import get_supabase_client
from supabase import Client


class BaseRepository:
    """Base repository providing a shared Supabase connection.

    Specialized repositories inherit from this class to obtain a
    configured Supabase client for persistence queries.

    Attributes:
        supabase: Configured Supabase client.
    """

    def __init__(self, supabase: Client | None = None):
        """Initialize the repository with an injected or default client.

        Args:
            supabase: Optional pre-built Supabase client; defaults to the
                factory-provided connection.
        """
        self.supabase = supabase or get_supabase_client()
