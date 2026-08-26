"""Testes anti-leakage do dataset builder — os mais críticos do marco de ML."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from app.ml.dataset import MLDataset, build_dataset, finalize_training_frame
from tests.ml.synthetic import dataset_config, make_market


def _single_symbol(closes: list[float], start: str = "2024-01-01") -> tuple:
    dates = pd.date_range(start, periods=len(closes), freq="D", tz="UTC")
    klines = pd.DataFrame(
        {"symbol": "AAAUSDT", "open_time": dates, "close": closes, "volume": 100.0}
    )
    features = pd.DataFrame(
        {
            "symbol": "AAAUSDT",
            "timestamp": dates,
            "rsi_14": 50.0,
            "sma_20": closes,
            "atr_14": 1.0,
            "volume_sma_20": 100.0,
        }
    )
    return features, klines


class TargetConstructionTests(unittest.TestCase):
    def test_targets_are_exact_forward_log_returns(self):
        closes = [100.0, 110.0, 121.0, 133.1, 146.41]
        features, klines = _single_symbol(closes)
        dataset = build_dataset(features, klines, dataset_config(horizons=[1, 2]))
        frame = dataset.frame
        # y_1 em t é exatamente log(close_{t+1}/close_t); série cresce 10% ao dia.
        expected = np.log(1.1)
        for row in range(len(closes) - 1):
            self.assertAlmostEqual(frame.loc[row, "y_1"], expected, places=12)
        for row in range(len(closes) - 2):
            self.assertAlmostEqual(frame.loc[row, "y_2"], 2 * expected, places=12)
        # A cauda sem futuro suficiente fica NaN — nunca inventada.
        self.assertTrue(np.isnan(frame.loc[len(closes) - 1, "y_1"]))
        self.assertTrue(np.isnan(frame.loc[len(closes) - 2, "y_2"]))

    def test_gap_in_series_yields_nan_target_not_stretched_horizon(self):
        closes = [100.0, 110.0, 121.0, 133.1, 146.41]
        features, klines = _single_symbol(closes)
        # Remove o dia 2 (2024-01-03) das duas fontes: gap real de coleta.
        gap_day = pd.Timestamp("2024-01-03", tz="UTC")
        features = features[features["timestamp"] != gap_day]
        klines = klines[klines["open_time"] != gap_day]
        dataset = build_dataset(features, klines, dataset_config(horizons=[1, 2]))
        frame = dataset.frame.set_index("timestamp")
        # y_1 do dia anterior ao gap seria o retorno até o dia faltante → NaN,
        # jamais o retorno de 2 dias disfarçado de 1.
        self.assertTrue(np.isnan(frame.loc[pd.Timestamp("2024-01-02", tz="UTC"), "y_1"]))
        # y_2 do mesmo dia pula o gap e alcança 2024-01-04: 2 dias exatos de calendário.
        self.assertAlmostEqual(
            frame.loc[pd.Timestamp("2024-01-02", tz="UTC"), "y_2"],
            np.log(133.1 / 110.0),
            places=12,
        )
        # log_return do dia seguinte ao gap também é NaN (véspera ausente).
        self.assertTrue(np.isnan(frame.loc[pd.Timestamp("2024-01-04", tz="UTC"), "log_return"]))


class OpenCandleTests(unittest.TestCase):
    def test_open_candle_is_excluded_as_of_run_time(self):
        closes = [100.0, 110.0, 121.0, 133.1]
        features, klines = _single_symbol(closes)
        klines["close_time"] = (
            klines["open_time"] + pd.Timedelta(days=1) - pd.Timedelta(milliseconds=1)
        )
        # Job às 00:05 do dia da última vela: ela ainda está aberta.
        as_of = pd.Timestamp("2024-01-04T00:05:00", tz="UTC")
        dataset = build_dataset(features, klines, dataset_config(horizons=[1, 2]), as_of=as_of)
        self.assertEqual(dataset.frame["timestamp"].max(), pd.Timestamp("2024-01-03", tz="UTC"))
        # Sem as_of (ou sem close_time) nada é filtrado — contrato explícito.
        full = build_dataset(features, klines, dataset_config(horizons=[1, 2]))
        self.assertEqual(full.frame["timestamp"].max(), pd.Timestamp("2024-01-04", tz="UTC"))

    def test_only_open_candles_raises(self):
        features, klines = _single_symbol([100.0])
        klines["close_time"] = klines["open_time"] + pd.Timedelta(days=1)
        with self.assertRaises(ValueError):
            build_dataset(
                features, klines, dataset_config(), as_of=pd.Timestamp("2024-01-01", tz="UTC")
            )


class LeakageInvarianceTests(unittest.TestCase):
    def test_features_are_invariant_to_future_truncation(self):
        """Cortar o futuro não pode mudar nenhuma feature do passado.

        Pega qualquer uso acidental de informação futura no builder (janela
        centrada, normalização global, estatística do painel inteiro).
        """
        features, klines = make_market(days=120, seed=7)
        config = dataset_config()
        cutoff = pd.Timestamp("2024-03-01", tz="UTC")

        full = build_dataset(features, klines, config)
        truncated = build_dataset(
            features[features["timestamp"] <= cutoff],
            klines[klines["open_time"] <= cutoff],
            config,
        )

        full_past = (
            full.frame[full.frame["timestamp"] <= cutoff]
            .sort_values(["symbol", "timestamp"])
            .reset_index(drop=True)
        )
        truncated_past = truncated.frame.sort_values(["symbol", "timestamp"]).reset_index(drop=True)
        columns = ["symbol", "timestamp", "close", *full.feature_columns]
        pd.testing.assert_frame_equal(full_past[columns], truncated_past[columns])

    def test_transformed_features_are_scale_invariant(self):
        """Multiplicar todos os preços por 1000 não muda as features do modelo global."""
        features, klines = make_market(symbols=("AAAUSDT",), days=90, seed=3)
        config = dataset_config()
        base = build_dataset(features, klines, config)

        scaled_features = features.copy()
        scaled_klines = klines.copy()
        for column in ("sma_20", "atr_14"):
            scaled_features[column] = scaled_features[column] * 1000.0
        scaled_klines["close"] = scaled_klines["close"] * 1000.0
        scaled = build_dataset(scaled_features, scaled_klines, config)

        pd.testing.assert_frame_equal(
            base.frame[list(base.feature_columns)],
            scaled.frame[list(scaled.feature_columns)],
        )

    def test_target_columns_never_appear_as_features(self):
        features, klines = make_market(days=90)
        dataset = build_dataset(features, klines, dataset_config())
        self.assertFalse(set(dataset.feature_columns) & set(dataset.target_columns))


class InputValidationTests(unittest.TestCase):
    def test_duplicate_symbol_timestamp_is_rejected(self):
        features, klines = make_market(symbols=("AAAUSDT",), days=30)
        duplicated = pd.concat([klines, klines.tail(1)], ignore_index=True)
        with self.assertRaises(ValueError):
            build_dataset(features, duplicated, dataset_config())

    def test_missing_required_columns_are_rejected(self):
        features, klines = make_market(symbols=("AAAUSDT",), days=30)
        with self.assertRaises(ValueError):
            build_dataset(features, klines.drop(columns=["close"]), dataset_config())

    def test_empty_inputs_are_rejected(self):
        features, klines = make_market(symbols=("AAAUSDT",), days=30)
        with self.assertRaises(ValueError):
            build_dataset(features.iloc[0:0], klines, dataset_config())


class FinalizeTrainingFrameTests(unittest.TestCase):
    def _dataset_and_train_dates(self, **config_overrides) -> tuple[MLDataset, pd.DatetimeIndex]:
        features, klines = make_market(days=120, seed=11)
        config = dataset_config(**config_overrides)
        dataset = build_dataset(features, klines, config)
        dates = pd.DatetimeIndex(dataset.frame["timestamp"].unique()).sort_values()
        return dataset, dates[: len(dates) * 2 // 3]

    def test_warmup_rows_are_dropped(self):
        dataset, train_dates = self._dataset_and_train_dates()
        final = finalize_training_frame(dataset, train_dates, dataset_config())
        self.assertFalse(final.frame[list(final.feature_columns)].isna().any().any())
        self.assertFalse(final.frame[list(final.target_columns)].isna().any().any())
        # As primeiras 19 velas de cada símbolo não têm sma_20 — não podem sobrar.
        first_kept = final.frame.groupby("symbol")["timestamp"].min().min()
        self.assertGreater(first_kept, pd.Timestamp("2024-01-19", tz="UTC"))

    def test_null_fraction_is_measured_on_train_rows_only(self):
        dataset, train_dates = self._dataset_and_train_dates()
        frame = dataset.frame.copy()
        # Coluna nula no TREINO inteiro mas preenchida depois: a fração global
        # fica abaixo do corte, só a medição train-only a derruba.
        frame["rsi_14"] = frame["rsi_14"].where(~frame["timestamp"].isin(train_dates), np.nan)
        poisoned = MLDataset(
            frame=frame,
            feature_columns=dataset.feature_columns,
            target_columns=dataset.target_columns,
        )
        global_fraction = frame["rsi_14"].isna().mean()
        self.assertLess(0.3, global_fraction)  # sanity: no treino é 100% nula
        final = finalize_training_frame(poisoned, train_dates, dataset_config())
        self.assertNotIn("rsi_14", final.feature_columns)

    def test_symbols_with_short_history_are_excluded(self):
        features, klines = make_market(days=120, seed=5)
        # BBBUSDT "listada" faltando poucos dias para o fim do treino.
        listing = pd.Timestamp("2024-03-20", tz="UTC")
        features = features[(features["symbol"] != "BBBUSDT") | (features["timestamp"] >= listing)]
        klines = klines[(klines["symbol"] != "BBBUSDT") | (klines["open_time"] >= listing)]
        config = dataset_config(min_history_days=30)
        dataset = build_dataset(features, klines, config)
        dates = pd.DatetimeIndex(dataset.frame["timestamp"].unique()).sort_values()
        train_dates = dates[dates <= pd.Timestamp("2024-04-01", tz="UTC")]
        final = finalize_training_frame(dataset, train_dates, config)
        self.assertEqual(set(final.frame["symbol"]), {"AAAUSDT"})

    def test_no_train_rows_raises(self):
        dataset, _ = self._dataset_and_train_dates()
        alien_dates = pd.DatetimeIndex([pd.Timestamp("1999-01-01", tz="UTC")])
        with self.assertRaises(ValueError):
            finalize_training_frame(dataset, alien_dates, dataset_config())


if __name__ == "__main__":
    unittest.main()
