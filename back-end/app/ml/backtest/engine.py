"""Backtest econômico long/flat sobre previsões de log-retorno h=1.

Convenções (honestas, sem lookahead):

- O sinal em t usa apenas informação disponível no fechamento de t (as features
  da linha t). A posição decidida em t captura o retorno de close_t → close_{t+1}
  (exatamente o target ``y_1``). Não há "abertura de t+1" no dataset diário; o
  custo de não executar exatamente no close é modelado pelo ``slippage_pct``.
- Custos: cada mudança de posição paga ``fee_pct + slippage_pct`` sobre o
  notional, aplicada em log (log(1 − custo)).
- Carteira: pesos iguais entre os símbolos presentes em cada dia.

Métricas em cima da curva de equity: ROI, Sharpe anualizado (365d), max
drawdown e nº de trades — sempre lado a lado com buy-and-hold.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.ml.config import BacktestConfig

_TRADING_DAYS_PER_YEAR = 365  # cripto negocia todo dia


@dataclass(frozen=True)
class BacktestResult:
    equity_curve: pd.Series  # equity da carteira por data (base 1.0)
    roi: float
    sharpe: float
    max_drawdown: float
    n_trades: int
    buy_hold_roi: float
    buy_hold_sharpe: float
    buy_hold_max_drawdown: float


def run_backtest(
    frame: pd.DataFrame,
    signals: pd.Series,
    config: BacktestConfig,
    threshold: float = 0.0,
) -> BacktestResult:
    """Simula long/flat: comprado quando o sinal supera o threshold, fora senão.

    ``frame`` precisa de symbol, timestamp e y_1 (retorno realizado t→t+1);
    ``signals`` é a previsão de y_1 alinhada pelo índice do frame.
    """
    if not frame.index.equals(signals.index):
        raise ValueError("frame e signals precisam ter o mesmo índice.")
    required = {"symbol", "timestamp", "y_1"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Backtest sem colunas: {', '.join(sorted(missing))}.")

    data = frame[["symbol", "timestamp", "y_1"]].copy()
    data["position"] = (signals > threshold).astype(float)
    cost_log = np.log1p(-(config.fee_pct + config.slippage_pct))

    strategy_parts = []
    hold_parts = []
    n_trades = 0
    for _, group in data.groupby("symbol", sort=True):
        ordered = group.sort_values("timestamp")
        position = ordered["position"]
        # Entrada/saída: mudança vs posição anterior (começa flat).
        changes = position.diff().abs().fillna(position.iloc[0])
        n_trades += int(changes.sum())
        strategy_log = position * ordered["y_1"] + changes * cost_log
        # Buy-and-hold paga o custo de entrada uma única vez.
        hold_log = ordered["y_1"].copy()
        hold_log.iloc[0] += cost_log
        strategy_parts.append(pd.Series(strategy_log.to_numpy(), index=ordered["timestamp"]))
        hold_parts.append(pd.Series(hold_log.to_numpy(), index=ordered["timestamp"]))

    strategy_daily = _portfolio_daily_log_returns(strategy_parts)
    hold_daily = _portfolio_daily_log_returns(hold_parts)

    equity_curve = np.exp(strategy_daily.cumsum())
    hold_curve = np.exp(hold_daily.cumsum())

    return BacktestResult(
        equity_curve=equity_curve,
        roi=float(equity_curve.iloc[-1] - 1.0),
        sharpe=_sharpe(strategy_daily),
        max_drawdown=_max_drawdown(equity_curve),
        n_trades=n_trades,
        buy_hold_roi=float(hold_curve.iloc[-1] - 1.0),
        buy_hold_sharpe=_sharpe(hold_daily),
        buy_hold_max_drawdown=_max_drawdown(hold_curve),
    )


def _portfolio_daily_log_returns(per_symbol: list[pd.Series]) -> pd.Series:
    """Peso igual entre os símbolos com dado no dia (média dos log-retornos)."""
    table = pd.concat(per_symbol, axis=1)
    daily = table.mean(axis=1, skipna=True)
    return daily.sort_index()


def _sharpe(daily_log_returns: pd.Series) -> float:
    simple = np.expm1(daily_log_returns)
    std = float(simple.std(ddof=0))
    if std == 0.0:
        return 0.0
    return float(simple.mean() / std * np.sqrt(_TRADING_DAYS_PER_YEAR))


def _max_drawdown(equity_curve: pd.Series) -> float:
    running_max = equity_curve.cummax()
    drawdown = equity_curve / running_max - 1.0
    return float(drawdown.min())
