"""Regras de vela compartilhadas por jobs de ML e API.

A coleta diária (00:05 UTC) guarda a vela do dia corrente ainda aberta — um
"close" parcial que não pode virar origem de previsão, target, realização nem
ponto observado no gráfico. Todo consumidor de ``klines_1d`` filtra por
``close_time`` (ADR-0004).
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def drop_open_candles(klines: pd.DataFrame, as_of: pd.Timestamp | None) -> pd.DataFrame:
    """Mantém apenas velas com ``close_time <= as_of`` (sem close_time, mantém tudo)."""
    if as_of is None or "close_time" not in klines.columns:
        return klines
    closed = pd.to_datetime(klines["close_time"], utc=True) <= as_of
    if not closed.all():
        logger.info("%s velas ainda abertas em %s ignoradas.", int((~closed).sum()), as_of)
    return klines[closed]
