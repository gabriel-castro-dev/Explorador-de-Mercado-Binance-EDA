"""Geradores de mercado sintético para os testes offline do pipeline de ML."""

import numpy as np
import pandas as pd

from app.ml.config import DatasetConfig, MLConfig


def dataset_config(**overrides) -> DatasetConfig:
    base = {
        "timeframe": "1d",
        "horizons": [1, 2],
        "lookback_window": 5,
        "min_history_days": 10,
        "max_null_fraction": 0.3,
    }
    base.update(overrides)
    return DatasetConfig.model_validate(base)


def ml_config(**dataset_overrides) -> MLConfig:
    return MLConfig.model_validate(
        {
            "dataset": dataset_config(**dataset_overrides).model_dump(),
            "splits": {"embargo_days": 2, "validation_days": 20, "n_folds": 2},
            "training": {"seed": 42, "clip_sigma": 10.0},
            "gate": {"min_skill_score": 0.0},
            "backtest": {"fee_pct": 0.001, "slippage_pct": 0.0005},
            "monitoring": {"lookback_days": 30, "degradation_runs": 3, "min_scored_rows": 5},
        }
    )


def make_drift_market(
    drifts: dict[str, float],
    start: str = "2024-01-01",
    days: int = 200,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Mercado determinístico: cada símbolo cresce a um log-retorno diário fixo.

    Sem janelas móveis (sma = close, resto constante), então não há warm-up e os
    targets são exatamente ``h * drift`` — resposta fechada para os testes.
    """
    dates = pd.date_range(start, periods=days, freq="D", tz="UTC")
    klines_rows = []
    features_rows = []
    for symbol, drift in drifts.items():
        close = 100.0 * np.exp(drift * np.arange(days))
        klines_rows.append(
            pd.DataFrame({"symbol": symbol, "open_time": dates, "close": close, "volume": 100.0})
        )
        features_rows.append(
            pd.DataFrame(
                {
                    "symbol": symbol,
                    "timestamp": dates,
                    "sma_20": close,
                    "rsi_14": 50.0,
                    "atr_14": 1.0,
                    "volume_sma_20": 100.0,
                }
            )
        )
    return pd.concat(features_rows, ignore_index=True), pd.concat(klines_rows, ignore_index=True)


def make_market(
    symbols: tuple[str, ...] = ("AAAUSDT", "BBBUSDT"),
    start: str = "2024-01-01",
    days: int = 120,
    seed: int = 0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Klines diárias + features estilo features_24h, determinísticas por seed.

    As janelas móveis (sma_20, volume_sma_20) produzem o warm-up NaN real do
    pipeline; rsi_14 e atr_14 cobrem os grupos scale-free e price-scale.
    """
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start, periods=days, freq="D", tz="UTC")
    klines_rows = []
    features_rows = []
    for index, symbol in enumerate(symbols):
        close = pd.Series(
            100.0 * (index + 1) * np.exp(np.cumsum(rng.normal(0.0, 0.02, days))),
            index=dates,
        )
        volume = pd.Series(rng.uniform(50.0, 150.0, days), index=dates)
        klines_rows.append(
            pd.DataFrame(
                {
                    "symbol": symbol,
                    "open_time": dates,
                    "close": close.to_numpy(),
                    "volume": volume.to_numpy(),
                }
            )
        )
        features_rows.append(
            pd.DataFrame(
                {
                    "symbol": symbol,
                    "timestamp": dates,
                    "sma_20": close.rolling(20).mean().to_numpy(),
                    "rsi_14": (50.0 + 10.0 * np.sin(np.arange(days) / 7.0)),
                    "atr_14": (close * 0.02).to_numpy(),
                    "volume_sma_20": volume.rolling(20).mean().to_numpy(),
                }
            )
        )
    return pd.concat(features_rows, ignore_index=True), pd.concat(klines_rows, ignore_index=True)
