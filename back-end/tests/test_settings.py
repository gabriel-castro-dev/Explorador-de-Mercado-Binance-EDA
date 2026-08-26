"""Settings: variáveis só são exigidas por quem conecta de fato (AGENTS.md)."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import Settings, get_settings

_SUPABASE_ONLY = {"SUPABASE_URL": "https://test-project.supabase.co", "SUPABASE_KEY": "service"}


class SettingsTests(unittest.TestCase):
    def tearDown(self):
        get_settings.cache_clear()

    def test_supabase_only_job_loads_without_binance_keys(self):
        with patch.dict(os.environ, _SUPABASE_ONLY, clear=True):
            settings = Settings(_env_file=None)
        self.assertIsNone(settings.BINANCE_API_KEY)
        self.assertIsNone(settings.BINANCE_API_SECRET)

    def test_binance_client_fails_clearly_without_keys(self):
        from app.clients.binance_client import BinanceClient

        with patch.dict(os.environ, _SUPABASE_ONLY, clear=True):
            get_settings.cache_clear()
            with patch("config.Settings.model_config", {"env_file": None}):
                with self.assertRaisesRegex(RuntimeError, "BINANCE_API_KEY"):
                    BinanceClient()


if __name__ == "__main__":
    unittest.main()
