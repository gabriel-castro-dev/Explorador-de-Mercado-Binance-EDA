"""Carregamento e validação da configuração do pipeline de ML (ml.yml)."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

_CONFIG_PATH = Path(__file__).resolve().parent / "ml.yml"


class DatasetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timeframe: str = "1d"
    horizons: list[int] = Field(min_length=1)
    lookback_window: int = Field(gt=0)
    min_history_days: int = Field(gt=0)
    max_null_fraction: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def _check_horizons(self) -> "DatasetConfig":
        if sorted(self.horizons) != self.horizons:
            raise ValueError("horizons deve estar em ordem crescente.")
        if len(set(self.horizons)) != len(self.horizons):
            raise ValueError("horizons não pode ter duplicatas.")
        if self.horizons[0] < 1:
            raise ValueError("horizons deve começar em 1 ou mais.")
        if self.min_history_days <= self.lookback_window:
            raise ValueError("min_history_days deve exceder lookback_window.")
        return self


class SplitsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    embargo_days: int = Field(gt=0)
    validation_days: int = Field(gt=0)
    n_folds: int = Field(gt=0)

    @model_validator(mode="after")
    def _folds_divide_validation(self) -> "SplitsConfig":
        if self.validation_days % self.n_folds != 0:
            raise ValueError("validation_days deve ser múltiplo de n_folds.")
        return self

    @property
    def fold_days(self) -> int:
        return self.validation_days // self.n_folds


class TrainingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seed: int
    clip_sigma: float = Field(gt=0)


class GateConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_skill_score: float


class BacktestConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fee_pct: float = Field(ge=0)
    slippage_pct: float = Field(ge=0)


class MonitoringConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lookback_days: int = Field(gt=0)
    degradation_runs: int = Field(gt=0)
    min_scored_rows: int = Field(gt=0)


class MLConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset: DatasetConfig
    splits: SplitsConfig
    training: TrainingConfig
    gate: GateConfig
    backtest: BacktestConfig
    monitoring: MonitoringConfig
    models: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _embargo_covers_horizons(self) -> "MLConfig":
        # Invariante anti-leakage: um target y_h = log(close_{t+h}/close_t) criado
        # no fim do treino não pode alcançar datas da validação. O embargo tem de
        # cobrir o maior horizonte.
        max_horizon = max(self.dataset.horizons)
        if self.splits.embargo_days < max_horizon:
            raise ValueError(
                f"embargo_days ({self.splits.embargo_days}) deve ser >= "
                f"max(horizons) ({max_horizon}) para impedir vazamento temporal."
            )
        return self


def load_ml_config(config_path: Path = _CONFIG_PATH) -> MLConfig:
    """Load and validate the ML pipeline configuration."""
    with config_path.open(encoding="utf-8") as config_file:
        raw = yaml.safe_load(config_file) or {}
    return MLConfig.model_validate(raw)
