from app.clients.supabase_client import get_supabase_client


class BaseRepository:
    """Base repository providing a shared Supabase connection.

    Specialized repositories inherit from this class to obtain a
    configured Supabase client for persistence queries.

    Attributes:
        supabase: Configured Supabase client.
    """

    def __init__(self):
        """Initialize the base repository with a Supabase client."""
        self.supabase = get_supabase_client()