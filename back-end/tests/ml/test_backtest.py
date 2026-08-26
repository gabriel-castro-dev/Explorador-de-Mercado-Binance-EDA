"""Backtest: PnL fechado na mão, custos exatos e ausência de lookahead."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from app.ml.backtest.engine import run_backtest
from app.ml.config import BacktestConfig

_COST = BacktestConfig(fee_pct=0.001, slippage_pct=0.0005)
_FREE = BacktestConfig(fee_pct=0.0, slippage_pct=0.0)


def _single_symbol_frame(returns: list[float]) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=len(returns), freq="D", tz="UTC")
    return pd.DataFrame({"symbol": "AAAUSDT", "timestamp": dates, "y_1": returns})


class BacktestClosedFormTests(unittest.TestCase):
    def test_perfect_foresight_matches_hand_computation(self):
        frame = _single_symbol_frame([0.10, -0.05, 0.20])
        signal = frame["y_1"]  # foresight perfeito
        result = run_backtest(frame, signal, _COST)
        cost_log = np.log1p(-0.0015)
        # Posições [1, 0, 1] → 3 mudanças; captura só os retornos positivos.
        self.assertEqual(result.n_trades, 3)
        self.assertAlmostEqual(result.roi, np.exp(0.30 + 3 * cost_log) - 1.0, places=12)
        # Buy-and-hold: tudo, com um único custo de entrada.
        self.assertAlmostEqual(result.buy_hold_roi, np.exp(0.25 + cost_log) - 1.0, places=12)

    def test_costs_reduce_pnl_by_exact_amount(self):
        frame = _single_symbol_frame([0.10, -0.05, 0.20])
        signal = frame["y_1"]
        with_costs = run_backtest(frame, signal, _COST)
        without_costs = run_backtest(frame, signal, _FREE)
        log_difference = np.log1p(without_costs.roi) - np.log1p(with_costs.roi)
        self.assertAlmostEqual(log_difference, -3 * np.log1p(-0.0015), places=12)

    def test_no_lookahead_shifted_signal_changes_result(self):
        rng = np.random.default_rng(0)
        returns = rng.normal(0.0, 0.03, 60).tolist()
        frame = _single_symbol_frame(returns)
        perfect = frame["y_1"]
        shifted = perfect.shift(1).fillna(0.0)  # "previsão" do retorno de ontem
        perfect_result = run_backtest(frame, perfect, _FREE)
        shifted_result = run_backtest(frame, shifted, _FREE)
        self.assertNotAlmostEqual(perfect_result.roi, shifted_result.roi, places=6)
        # Foresight perfeito domina qualquer sinal atrasado.
        self.assertGreater(perfect_result.roi, shifted_result.roi)

    def test_max_drawdown_on_known_curve(self):
        frame = _single_symbol_frame([0.10, -0.05, 0.20])
        always_long = pd.Series(1.0, index=frame.index)
        result = run_backtest(frame, always_long, _FREE)
        self.assertAlmostEqual(result.max_drawdown, np.exp(-0.05) - 1.0, places=12)

    def test_flat_strategy_has_zero_roi_and_trades(self):
        frame = _single_symbol_frame([0.10, -0.05, 0.20])
        never_long = pd.Series(-1.0, index=frame.index)
        result = run_backtest(frame, never_long, _COST)
        self.assertEqual(result.n_trades, 0)
        self.assertAlmostEqual(result.roi, 0.0, places=12)


class BacktestPortfolioTests(unittest.TestCase):
    def test_equal_weight_across_symbols(self):
        dates = pd.date_range("2024-01-01", periods=2, freq="D", tz="UTC")
        frame = pd.DataFrame(
            {
                "symbol": ["AAAUSDT", "AAAUSDT", "BBBUSDT", "BBBUSDT"],
                "timestamp": list(dates) * 2,
                "y_1": [0.10, 0.20, -0.02, 0.04],
            }
        )
        always_long = pd.Series(1.0, index=frame.index)
        result = run_backtest(frame, always_long, _FREE)
        expected_log = (0.10 + -0.02) / 2 + (0.20 + 0.04) / 2
        self.assertAlmostEqual(result.roi, np.exp(expected_log) - 1.0, places=12)

    def test_index_mismatch_is_rejected(self):
        frame = _single_symbol_frame([0.1, 0.2]).set_axis([10, 11])
        with self.assertRaises(ValueError):
            run_backtest(frame, frame["y_1"].reset_index(drop=True), _FREE)


if __name__ == "__main__":
    unittest.main()
