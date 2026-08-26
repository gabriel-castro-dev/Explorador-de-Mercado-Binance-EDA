"""CLI do pipeline de ML: treino diário + publicação e backtest econômico.

Comandos (mesmo padrão de exit codes dos jobs: 0 sucesso, 1 falha):

- ``train-predict`` — treina os candidatos, seleciona o campeão, aplica o gate e
  publica previsões + métricas no Supabase (fallback naive marcado se reprovar).
- ``backtest`` — roda a mesma avaliação, imprime o backtest econômico do
  campeão na validação (long/flat com custos vs buy-and-hold) e anexa o
  relatório em ``docs/ml/experiments.md``, sem tocar no banco.
- ``evaluate`` — pontua previsões passadas contra o close realizado, grava
  ``realized_metrics`` e sai com 1 se o modelo perde do naive por K rodadas.

Uso: ``uv run python -m app.ml.main train-predict``
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import pandas as pd

from app.core.timeframe import Timeframe
from app.ml.backtest.engine import run_backtest
from app.ml.config import MLConfig, load_ml_config
from app.ml.inference import build_fallback_rows, build_forecast_rows, build_metrics_record
from app.ml.monitoring import detect_degradation, score_predictions
from app.ml.training import run_training
from app.repositories.features_repository import FeaturesRepository
from app.repositories.forecast_repository import ForecastRepository
from app.repositories.klines_repository import KlinesRepository
from config import setup_logging

logger = logging.getLogger(__name__)
_EXPERIMENTS_LOG = Path(__file__).resolve().parents[3] / "docs" / "ml" / "experiments.md"


def run_train_predict(
    features_repo: FeaturesRepository | None = None,
    klines_repo: KlinesRepository | None = None,
    forecast_repo: ForecastRepository | None = None,
    config: MLConfig | None = None,
    git_sha: str | None = None,
    now: pd.Timestamp | None = None,
    factories: dict | None = None,
) -> int:
    config = config or load_ml_config()
    features_repo = features_repo or FeaturesRepository()
    klines_repo = klines_repo or KlinesRepository()
    forecast_repo = forecast_repo or ForecastRepository()
    git_sha = git_sha or os.environ.get("GITHUB_SHA", "local")
    now = now or pd.Timestamp.now(tz="UTC")

    features = features_repo.get_all_features(Timeframe.D1)
    klines = klines_repo.get_latest_klines(Timeframe.D1.value)
    outcome = run_training(
        features, klines, config, git_sha=git_sha, run_date=now, factories=factories
    )

    if outcome.gate.passed:
        rows = build_forecast_rows(outcome, run_at=now)
        published_fallback = False
    else:
        logger.warning(
            "Gate reprovou o campeão (%s) — publicando fallback naive. %s",
            outcome.champion.name,
            outcome.gate.reason,
        )
        rows = build_fallback_rows(outcome, run_at=now)
        published_fallback = True

    forecast_repo.upsert_predictions(rows)
    forecast_repo.upsert_model_metrics(
        build_metrics_record(outcome, now, git_sha, published_fallback)
    )
    logger.info(
        "Rodada publicada: model_version=%s, campeão=%s, skill=%.4f, fallback=%s.",
        outcome.model_version,
        outcome.champion.name,
        outcome.gate.skill,
        published_fallback,
    )
    return 0


def run_backtest_report(
    features_repo: FeaturesRepository | None = None,
    klines_repo: KlinesRepository | None = None,
    config: MLConfig | None = None,
    report_path: Path | None = None,
    now: pd.Timestamp | None = None,
    factories: dict | None = None,
) -> int:
    config = config or load_ml_config()
    features_repo = features_repo or FeaturesRepository()
    klines_repo = klines_repo or KlinesRepository()
    report_path = report_path or _EXPERIMENTS_LOG
    now = now or pd.Timestamp.now(tz="UTC")

    features = features_repo.get_all_features(Timeframe.D1)
    klines = klines_repo.get_latest_klines(Timeframe.D1.value)
    outcome = run_training(
        features, klines, config, git_sha="backtest", run_date=now, factories=factories
    )
    result = run_backtest(
        outcome.validation_frame,
        outcome.validation_predictions["y_1"],
        config.backtest,
    )
    logger.info(
        "Backtest do campeão %s na validação — ROI %.2f%% (buy-and-hold %.2f%%), "
        "Sharpe %.2f (b&h %.2f), max drawdown %.2f%% (b&h %.2f%%), %s trades.",
        outcome.champion.name,
        result.roi * 100,
        result.buy_hold_roi * 100,
        result.sharpe,
        result.buy_hold_sharpe,
        result.max_drawdown * 100,
        result.buy_hold_max_drawdown * 100,
        result.n_trades,
    )
    _append_backtest_report(report_path, outcome, result, now)
    return 0


def _append_backtest_report(path: Path, outcome, result, now: pd.Timestamp) -> None:
    """Relatório determinístico (dado o mesmo dataset/seed) anexado ao log de experimentos."""
    ranking = ", ".join(f"{name} {skill:+.4f}" for name, skill in outcome.champion.ranking.items())
    folds = ", ".join(f"{skill:+.4f}" for skill in outcome.fold_skills)
    lines = [
        "",
        f"## BT-{now:%Y%m%d} — backtest do campeão `{outcome.champion.name}` (validação)",
        f"- Data: {now:%Y-%m-%d} · Treino: {outcome.train_start:%Y-%m-%d} → {outcome.train_end:%Y-%m-%d}",
        f"- Ranking (skill h1 vs naive): {ranking}",
        f"- Skill h1 por fold: {folds}",
        f"- Gate: {outcome.gate.reason}",
        f"- Estratégia long/flat: ROI {result.roi * 100:.2f}% · Sharpe {result.sharpe:.2f} · "
        f"max drawdown {result.max_drawdown * 100:.2f}% · {result.n_trades} trades",
        f"- Buy-and-hold: ROI {result.buy_hold_roi * 100:.2f}% · Sharpe {result.buy_hold_sharpe:.2f} · "
        f"max drawdown {result.buy_hold_max_drawdown * 100:.2f}%",
    ]
    with path.open("a", encoding="utf-8") as report:
        report.write("\n".join(lines) + "\n")
    logger.info("Relatório de backtest anexado em %s.", path)


def run_evaluate(
    klines_repo: KlinesRepository | None = None,
    forecast_repo: ForecastRepository | None = None,
    config: MLConfig | None = None,
    now: pd.Timestamp | None = None,
) -> int:
    """Pontua previsões passadas contra o realizado; falha alto em degradação."""
    config = config or load_ml_config()
    klines_repo = klines_repo or KlinesRepository()
    forecast_repo = forecast_repo or ForecastRepository()
    now = now or pd.Timestamp.now(tz="UTC")

    since = now - pd.Timedelta(days=config.monitoring.lookback_days)
    predictions = forecast_repo.get_scoreable_predictions(now=now, since=since)
    if not predictions:
        logger.info(
            "Nenhuma previsão realizada para pontuar na janela de %s dias.",
            config.monitoring.lookback_days,
        )
        return 0

    klines = klines_repo.get_latest_klines(Timeframe.D1.value)
    scores = score_predictions(predictions, klines, config.monitoring, as_of=now)
    for score in scores:
        forecast_repo.update_realized_metrics(
            score.model_version, score.to_payload(computed_at=now)
        )
        logger.info(
            "model_version=%s: skill realizado h1=%s (%s linhas pontuadas).",
            score.model_version,
            f"{score.skill_h1:.4f}" if score.skill_h1 is not None else "n/a",
            score.n_rows,
        )
        if score.is_degenerate and not score.is_fallback:
            logger.warning(
                "model_version=%s publicou previsões degeneradas (variância ~zero) "
                "sem estar marcada como fallback — naive disfarçado.",
                score.model_version,
            )

    if detect_degradation(scores, config.monitoring):
        logger.error(
            "DEGRADAÇÃO: as últimas %s versões pontuadas perderam do naive no "
            "realizado (h=1). Investigar antes da próxima publicação.",
            config.monitoring.degradation_runs,
        )
        return 1
    return 0


_COMMANDS = {
    "train-predict": run_train_predict,
    "backtest": run_backtest_report,
    "evaluate": run_evaluate,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pipeline de ML/forecasting.")
    parser.add_argument("command", choices=sorted(_COMMANDS))
    arguments = parser.parse_args(argv)
    try:
        return _COMMANDS[arguments.command]()
    except Exception:
        logger.exception("Comando de ML '%s' falhou.", arguments.command)
        return 1


if __name__ == "__main__":
    setup_logging()
    sys.exit(main())
