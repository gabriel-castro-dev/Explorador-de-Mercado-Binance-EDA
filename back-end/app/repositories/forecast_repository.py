"""Persistence and reads for ML forecasts (predictions + model_metrics)."""

import logging
from datetime import datetime

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ForecastRepository(BaseRepository):
    _PREDICTIONS_TABLE = "predictions"
    _METRICS_TABLE = "model_metrics"
    _PREDICTIONS_CONFLICT = "symbol,target_time,horizon_days,model_version"
    _MONTE_CARLO_TABLE = "monte_carlo_runs"
    _MONTE_CARLO_CONFLICT = "symbol,model_version"

    def upsert_predictions(self, rows: list[dict]) -> int:
        """Idempotent upsert of forecast rows (same run twice → same table state)."""
        if not rows:
            logger.warning("Nenhuma previsão para persistir.")
            return 0
        self._upsert_in_batches(self._PREDICTIONS_TABLE, rows, self._PREDICTIONS_CONFLICT)
        logger.info("%s previsões persistidas em %s.", len(rows), self._PREDICTIONS_TABLE)
        return len(rows)

    def upsert_model_metrics(self, record: dict) -> None:
        """One row per model_version; re-running a version overwrites its metrics."""
        self.supabase.table(self._METRICS_TABLE).upsert(
            record, on_conflict="model_version"
        ).execute()
        logger.info("Métricas persistidas para model_version=%s.", record.get("model_version"))

    def _latest_run(self) -> dict | None:
        """``run_at`` and ``model_version`` of the most recent run (``None`` when empty)."""
        rows = (
            self.supabase.table(self._PREDICTIONS_TABLE)
            .select("run_at, model_version")
            .order("run_at", desc=True)
            .limit(1)
            .execute()
        ).data
        return rows[0] if rows else None

    def get_latest_run_predictions(self, symbol: str | None = None) -> list[dict]:
        """Rows of the most recent run (max run_at), optionally for one symbol."""
        latest = self._latest_run()
        if latest is None:
            return []
        run_at = latest["run_at"]
        query = (
            self.supabase.table(self._PREDICTIONS_TABLE)
            .select("*")
            .eq("run_at", run_at)
            .order("symbol")
            .order("horizon_days")
        )
        if symbol is not None:
            query = query.eq("symbol", symbol)
        return query.execute().data

    def upsert_monte_carlo(self, rows: list[dict]) -> int:
        """Idempotent upsert of one Monte Carlo cloud per (symbol, model_version)."""
        if not rows:
            logger.warning("Nenhuma nuvem de Monte Carlo para persistir.")
            return 0
        self._upsert_in_batches(self._MONTE_CARLO_TABLE, rows, self._MONTE_CARLO_CONFLICT)
        logger.info("%s nuvens persistidas em %s.", len(rows), self._MONTE_CARLO_TABLE)
        return len(rows)

    def get_latest_monte_carlo(self, symbol: str) -> dict | None:
        """Most recent cloud (max run_at) of one symbol; ``None`` when never simulated."""
        rows = (
            self.supabase.table(self._MONTE_CARLO_TABLE)
            .select("*")
            .eq("symbol", symbol)
            .order("run_at", desc=True)
            .limit(1)
            .execute()
        ).data
        return rows[0] if rows else None

    def get_model_type(self, model_version: str) -> str | None:
        """``model_metrics.model_type`` of one version (``None`` when the row is missing)."""
        rows = (
            self.supabase.table(self._METRICS_TABLE)
            .select("model_type")
            .eq("model_version", model_version)
            .limit(1)
            .execute()
        ).data
        return rows[0]["model_type"] if rows else None

    def get_latest_run_metrics(self) -> dict | None:
        """``model_metrics`` row of the version that signed the most recent run.

        ``None`` when there are no predictions yet (or the metrics row is missing).
        """
        latest = self._latest_run()
        if latest is None:
            return None
        rows = (
            self.supabase.table(self._METRICS_TABLE)
            .select("*")
            .eq("model_version", latest["model_version"])
            .limit(1)
            .execute()
        ).data
        return rows[0] if rows else None

    def get_scoreable_predictions(self, now: datetime, since: datetime) -> list[dict]:
        """Predictions from runs since ``since`` whose target_time is already realized."""
        return self._fetch_all(
            lambda: (
                self.supabase.table(self._PREDICTIONS_TABLE)
                .select("*")
                .gte("run_at", since.isoformat())
                .lte("target_time", now.isoformat())
                .order("run_at")
                .order("symbol")
            )
        )

    def update_realized_metrics(self, model_version: str, payload: dict) -> None:
        """Fill realized_metrics for one version without touching the other columns."""
        self.supabase.table(self._METRICS_TABLE).update({"realized_metrics": payload}).eq(
            "model_version", model_version
        ).execute()
        logger.info("Métricas realizadas gravadas para model_version=%s.", model_version)
