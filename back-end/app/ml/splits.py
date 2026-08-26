"""Janelas walk-forward por DATA com embargo.

Por que por data e não por linha: os 20 símbolos são fortemente correlacionados
no cross-section — uma linha de validação de ETHUSDT no dia D vaza informação
para uma linha de treino de BTCUSDT no mesmo dia D. Aqui uma data pertence a
exatamente um conjunto, para todos os símbolos.

Por que embargo: um target de treino em t alcança close(t + max(horizons)).
Exigimos ``primeira_data_avaliada − última_data_de_treino > embargo_days``
(estrito), então com embargo = max(horizons) o último target de treino termina
no máximo um dia antes da janela avaliada começar.
"""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class WalkForwardFold:
    train_dates: pd.DatetimeIndex
    eval_dates: pd.DatetimeIndex


def walk_forward_windows(
    dates: pd.DatetimeIndex,
    eval_days: int,
    embargo_days: int,
    n_folds: int,
    min_train_days: int = 1,
) -> list[WalkForwardFold]:
    """Janelas expanding-window: folds de avaliação contíguos no fim da série.

    O fold k avalia ``eval_days`` dias; o treino é todo o histórico até o embargo
    antes da janela. Folds são devolvidos em ordem cronológica e cobrem o fim da
    série sem sobreposição nem buraco entre janelas de avaliação.
    """
    if eval_days <= 0 or n_folds <= 0:
        raise ValueError("eval_days e n_folds devem ser positivos.")
    unique = _unique_sorted(dates)
    gap = pd.Timedelta(days=embargo_days + 1)
    last = unique[-1]

    folds: list[WalkForwardFold] = []
    for k in range(n_folds - 1, -1, -1):
        eval_end = last - pd.Timedelta(days=k * eval_days)
        eval_start = eval_end - pd.Timedelta(days=eval_days - 1)
        train_end = eval_start - gap
        train = unique[unique <= train_end]
        eval_block = unique[(unique >= eval_start) & (unique <= eval_end)]
        if len(train) < min_train_days:
            raise ValueError(
                f"Fold com apenas {len(train)} dias de treino (mínimo {min_train_days}) — "
                "reduza n_folds/eval_days ou o histórico é curto demais."
            )
        if eval_block.empty:
            raise ValueError("Fold walk-forward com janela de avaliação vazia.")
        folds.append(WalkForwardFold(train_dates=train, eval_dates=eval_block))
    return folds


def _unique_sorted(dates: pd.DatetimeIndex) -> pd.DatetimeIndex:
    unique = pd.DatetimeIndex(pd.Series(dates).drop_duplicates()).sort_values()
    if unique.empty:
        raise ValueError("Sem datas para particionar.")
    if unique.tz is None:
        raise ValueError("Datas do split devem ser tz-aware (UTC).")
    return unique
