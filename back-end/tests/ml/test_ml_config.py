import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pydantic import ValidationError

from app.ml.config import MLConfig, load_ml_config


def _valid_raw() -> dict:
    return {
        "dataset": {
            "timeframe": "1d",
            "horizons": [1, 2, 3, 4, 5, 6, 7],
            "lookback_window": 60,
            "min_history_days": 120,
            "max_null_fraction": 0.3,
        },
        "splits": {"embargo_days": 7, "validation_days": 180, "n_folds": 4},
        "training": {"seed": 42, "clip_sigma": 10.0},
        "gate": {"min_skill_score": 0.0},
        "backtest": {"fee_pct": 0.001, "slippage_pct": 0.0005},
        "monitoring": {"lookback_days": 30, "degradation_runs": 3, "min_scored_rows": 20},
    }


class MLPackageImportTests(unittest.TestCase):
    def test_import_has_no_side_effects(self):
        # Convenção do projeto: importar não pode exigir .env nem abrir conexão.
        # Se o import chegou até aqui sem levantar, o contrato está mantido.
        import app.ml
        import app.ml.backtest
        import app.ml.config
        import app.ml.evaluation
        import app.ml.models

        self.assertIsNotNone(app.ml)
        self.assertIsNotNone(app.ml.config)
        self.assertIsNotNone(app.ml.models)
        self.assertIsNotNone(app.ml.evaluation)
        self.assertIsNotNone(app.ml.backtest)


class MLConfigTests(unittest.TestCase):
    def test_repo_config_is_valid(self):
        config = load_ml_config()
        self.assertEqual(config.dataset.timeframe, "1d")
        self.assertEqual(config.dataset.horizons, [1, 2, 3, 4, 5, 6, 7])
        self.assertGreaterEqual(config.splits.embargo_days, max(config.dataset.horizons))

    def test_embargo_must_cover_max_horizon(self):
        raw = _valid_raw()
        raw["splits"]["embargo_days"] = 3  # < max(horizons) == 7
        with self.assertRaises(ValidationError):
            MLConfig.model_validate(raw)

    def test_horizons_must_be_sorted_unique_and_positive(self):
        for bad in ([3, 1, 2], [1, 1, 2], [0, 1]):
            raw = _valid_raw()
            raw["dataset"]["horizons"] = bad
            with self.assertRaises(ValidationError, msg=f"horizons={bad}"):
                MLConfig.model_validate(raw)

    def test_min_history_must_exceed_lookback(self):
        raw = _valid_raw()
        raw["dataset"]["min_history_days"] = 60  # == lookback_window
        with self.assertRaises(ValidationError):
            MLConfig.model_validate(raw)

    def test_unknown_keys_are_rejected(self):
        # extra="forbid": typo em ml.yml deve falhar alto, não ser ignorado.
        raw = _valid_raw()
        raw["dataset"]["lockback_window"] = 60
        with self.assertRaises(ValidationError):
            MLConfig.model_validate(raw)


if __name__ == "__main__":
    unittest.main()
