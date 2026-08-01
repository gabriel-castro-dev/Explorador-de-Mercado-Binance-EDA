from app.clients.supabase_client import get_supabase_client


class BaseRepository:
    def __init__(self):
        self.supabase = get_supabase_client()
