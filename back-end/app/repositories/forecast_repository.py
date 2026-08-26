"""Persistence and reads for ML forecasts (predictions + model_metrics)."""

import logging
from datetime import datetime

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ForecastRepository(BaseRepository):
    _PREDICTIONS_TABLE = "predictions"
    _METRICS_TABLE = "model_metrics"
    _PREDICTIONS_CONFLICT = "symbol,target_time,horizon_days,model_version"

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

    def get_latest_run_predictions(self, symbol: str | None = None) -> list[dict]:
        """Rows of the most recent run (max run_at), optionally for one symbol."""
        latest = (
            self.supabase.table(self._PREDICTIONS_TABLE)
            .select("run_at")
            .order("run_at", desc=True)
            .limit(1)
            .execute()
        ).data
        if not latest:
            return []
        run_at = latest[0]["run_at"]
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
