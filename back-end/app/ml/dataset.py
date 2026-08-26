"""Construção do dataset de ML: features_24h × klines_1d → X e y multi-horizonte.

Contrato anti-leakage deste módulo:

- Toda transformação de feature usa apenas a própria linha (razões vs close) ou o
  passado (log-retorno de 1 dia). Nada de janelas centradas ou estatísticas globais.
- Targets ``y_h = log(close_{t+h} / close_t)`` são calculados sobre um grid diário
  contínuo por símbolo — um gap na série vira target NaN, nunca um shift posicional
  que silenciosamente esticaria o horizonte.
- Decisões dependentes de dados (descarte de colunas por nulls, mínimo de histórico)
  ficam em :func:`finalize_training_frame`, parametrizadas pelas datas de TREINO —
  o builder em si não olha estatística nenhuma do conjunto.
"""

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.core.candles import drop_open_candles
from app.ml.config import DatasetConfig

logger = logging.getLogger(__name__)

# Colunas de features_24h já invariantes de escala (comparáveis entre símbolos).
SCALE_FREE_COLUMNS = (
    "rsi_14",
    "avg_price_deviation_sma20",
    "avg_price_deviation_sma50",
    "avg_price_deviation_sma200",
    "bb_width",
    "price_change_percent",
    "volume_change_24h",
    "order_imbalance",
)
# Níveis de preço: viram razão vs close (x/close − 1) — um modelo global não pode
# ver BTC a 100k e DOGE a 0.1 na mesma unidade.
PRICE_LEVEL_COLUMNS = (
    "sma_20",
    "sma_50",
    "sma_200",
    "ema_12",
    "ema_26",
    "bb_upper",
    "bb_middle",
    "bb_lower",
)
# Grandezas em escala de preço (diferenças/amplitudes): viram fração do close.
PRICE_SCALE_COLUMNS = ("macd", "macd_signal", "macd_histogram", "atr_14", "bid_ask_spread")

_DERIVED_COLUMNS = ("log_return", "rel_volume")


@dataclass(frozen=True)
class MLDataset:
    """Painel símbolo × dia com features transformadas e targets multi-horizonte."""

    frame: pd.DataFrame
    feature_columns: tuple[str, ...]
    target_columns: tuple[str, ...]


def target_column(horizon: int) -> str:
    return f"y_{horizon}"


def horizon_of(target: str) -> int:
    """Inverso de :func:`target_column` (``"y_7" -> 7``)."""
    prefix, _, digits = target.partition("_")
    if prefix != "y" or not digits.isdigit():
        raise ValueError(f"Coluna de target inválida: {target!r}.")
    return int(digits)


def build_dataset(
    features: pd.DataFrame,
    klines: pd.DataFrame,
    config: DatasetConfig,
    as_of: pd.Timestamp | None = None,
) -> MLDataset:
    """Join features_24h × klines_1d e derivação de X (escala-invariante) e y.

    Preserva nulls (warm-up, gaps, colunas ausentes no histórico) e linhas sem
    target completo — o recorte acontece em :func:`finalize_training_frame`,
    que precisa conhecer as datas de treino para não vazar.

    ``as_of`` exclui a vela ainda aberta: o job roda logo após 00:00 UTC e a
    coleta guarda a vela do dia corrente com minutos de negociação — um
    "close" parcial que não pode virar origem de previsão nem target.
    """
    if features.empty or klines.empty:
        raise ValueError("features e klines não podem ser vazios.")
    klines = drop_open_candles(klines, as_of)
    if klines.empty:
        raise ValueError("Nenhuma vela fechada até as_of.")

    feature_rows = _prepare(features, timestamp_column="timestamp", required=("symbol",))
    candle_rows = _prepare(
        klines, timestamp_column="open_time", required=("symbol", "close", "volume")
    )[["symbol", "timestamp", "close", "volume"]]

    merged = feature_rows.merge(candle_rows, on=["symbol", "timestamp"], how="inner")
    if merged.empty:
        raise ValueError("Join features × klines vazio: timestamps não se alinham.")

    horizons = tuple(config.horizons)
    parts = [
        _build_symbol_frame(group, horizons) for _, group in merged.groupby("symbol", sort=True)
    ]
    frame = pd.concat(parts, ignore_index=True)

    feature_columns = (
        tuple(
            column
            for column in (*SCALE_FREE_COLUMNS, *PRICE_LEVEL_COLUMNS, *PRICE_SCALE_COLUMNS)
            if column in frame.columns
        )
        + _DERIVED_COLUMNS
    )
    target_columns = tuple(target_column(h) for h in horizons)

    overlap = set(feature_columns) & set(target_columns)
    if overlap:
        raise ValueError(f"Colunas de target aparecendo como feature: {sorted(overlap)}.")

    ordered = ["symbol", "timestamp", "close", *feature_columns, *target_columns]
    return MLDataset(
        frame=frame[ordered],
        feature_columns=feature_columns,
        target_columns=target_columns,
    )


def finalize_training_frame(
    dataset: MLDataset, train_dates: pd.DatetimeIndex, config: DatasetConfig
) -> MLDataset:
    """Recorte para treino/avaliação: poda colunas e linhas sem vazar do futuro.

    - Colunas com fração de nulls acima de ``max_null_fraction`` **medida só nas
      linhas de treino** são descartadas (ex.: bid_ask_spread inexistente no
      histórico do backfill).
    - Linhas com qualquer feature ou target nulo caem (warm-up, gaps, cauda).
    - Símbolos com menos de ``min_history_days`` linhas válidas de treino saem
      por inteiro — pouco histórico só ensinaria ruído.
    """
    frame = dataset.frame
    train_mask = frame["timestamp"].isin(train_dates)
    if not train_mask.any():
        raise ValueError("Nenhuma linha do dataset cai nas datas de treino.")

    train_rows = frame.loc[train_mask]
    kept_columns = tuple(
        column
        for column in dataset.feature_columns
        if train_rows[column].isna().mean() <= config.max_null_fraction
    )
    dropped = set(dataset.feature_columns) - set(kept_columns)
    if dropped:
        logger.info("Features descartadas por excesso de nulls no treino: %s", sorted(dropped))
    if not kept_columns:
        raise ValueError("Nenhuma feature sobrou após o corte de nulls.")

    complete = frame.dropna(subset=[*kept_columns, *dataset.target_columns])

    train_counts = complete.loc[complete["timestamp"].isin(train_dates), "symbol"].value_counts()
    kept_symbols = train_counts[train_counts >= config.min_history_days].index
    excluded = sorted(set(complete["symbol"]) - set(kept_symbols))
    if excluded:
        logger.info(
            "Símbolos fora do treino por histórico curto (<%s dias): %s",
            config.min_history_days,
            excluded,
        )
    final = complete[complete["symbol"].isin(kept_symbols)].reset_index(drop=True)
    if final.empty:
        raise ValueError("Dataset final vazio após filtros de nulls e histórico mínimo.")

    ordered = ["symbol", "timestamp", "close", *kept_columns, *dataset.target_columns]
    return MLDataset(
        frame=final[ordered],
        feature_columns=kept_columns,
        target_columns=dataset.target_columns,
    )


def _prepare(df: pd.DataFrame, timestamp_column: str, required: tuple[str, ...]) -> pd.DataFrame:
    missing = {timestamp_column, *required} - set(df.columns)
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(sorted(missing))}.")
    prepared = df.rename(columns={timestamp_column: "timestamp"}).copy()
    prepared["timestamp"] = pd.to_datetime(
        prepared["timestamp"], errors="raise", utc=True
    ).dt.normalize()
    duplicated = prepared.duplicated(subset=["symbol", "timestamp"])
    if duplicated.any():
        sample = prepared.loc[duplicated, ["symbol", "timestamp"]].iloc[0]
        raise ValueError(
            f"Linhas duplicadas por (symbol, timestamp) — ex.: {sample['symbol']} "
            f"{sample['timestamp']:%Y-%m-%d}."
        )
    return prepared.sort_values(["symbol", "timestamp"])


def _build_symbol_frame(group: pd.DataFrame, horizons: tuple[int, ...]) -> pd.DataFrame:
    """Deriva features e targets de um símbolo sobre um grid diário contínuo."""
    indexed = group.set_index("timestamp").sort_index()
    grid = pd.date_range(indexed.index.min(), indexed.index.max(), freq="D", tz="UTC")
    panel = indexed.reindex(grid)
    panel["symbol"] = panel["symbol"].ffill()

    close = panel["close"]
    with np.errstate(divide="ignore", invalid="ignore"):
        panel["log_return"] = np.log(close / close.shift(1))
        for horizon in horizons:
            panel[target_column(horizon)] = np.log(close.shift(-horizon) / close)
        for column in PRICE_LEVEL_COLUMNS:
            if column in panel.columns:
                panel[column] = panel[column] / close - 1.0
        for column in PRICE_SCALE_COLUMNS:
            if column in panel.columns:
                panel[column] = panel[column] / close
        if "volume_sma_20" in panel.columns:
            panel["rel_volume"] = panel["volume"] / panel["volume_sma_20"] - 1.0
        else:
            panel["rel_volume"] = np.nan

    # Só as datas com vela real voltam — o grid contínuo serviu apenas para que
    # shift(h) signifique exatamente h dias de calendário.
    result = panel[close.notna()].reset_index(names="timestamp")
    return result.replace([np.inf, -np.inf], np.nan)
