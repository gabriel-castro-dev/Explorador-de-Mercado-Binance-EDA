"""Base support shared by feature engineering pipelines."""

import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from app.feature_engineering.transforms.registry import registry

logger = logging.getLogger(__name__)


class BasePipeline:
    """Load feature rules and apply registered transforms without mutating input.

    Reads the feature configuration from ``features.yml`` and applies the
    configured transforms to DataFrames, returning a new DataFrame.
    """

    _CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "features.yml"

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the pipeline and load the feature configuration.

        Args:
            config_path: Path to the YAML configuration file. Defaults to the
                built-in ``features.yml``.
        """
        path = config_path or self._CONFIG_PATH
        with path.open(encoding="utf-8") as config_file:
            loaded_config = yaml.safe_load(config_file)
        self.config: dict[str, Any] = loaded_config or {}

    def apply_transforms(self, df: pd.DataFrame, feature_group: str) -> pd.DataFrame:
        """Apply the configured YAML transforms and return a new DataFrame.

        Args:
            df: Source DataFrame with raw market data.
            feature_group: YAML key identifying the list of transforms to apply.

        Returns:
            Copy of the input DataFrame with the calculated feature columns.

        Raises:
            ValueError: If the feature group is not configured or is malformed.
        """
        if df.empty:
            logger.warning("DataFrame vazio para grupo de features %s.", feature_group)
            return df.copy()
        try:
            transforms = self.config[feature_group]
        except KeyError as error:
            raise ValueError(
                f"Grupo de features não configurado: {feature_group!r}."
            ) from error
        if not isinstance(transforms, list):
            raise ValueError(f"Grupo de features inválido: {feature_group!r}.")

        result = df.copy()
        for transform in transforms:
            name, params = self._parse_transform(transform)
            if not self._has_required_columns(result, name):
                logger.warning(
                    "Transformação %s ignorada: colunas de origem ausentes.", name
                )
                continue
            values = registry.get(name)(result, **params)
            self._add_feature_columns(result, name, params, values)
        return result

    @staticmethod
    def _parse_transform(transform: object) -> tuple[str, dict[str, Any]]:
        """Parse a YAML transform entry into its name and parameters.

        Args:
            transform: Mapping from the YAML configuration describing a transform.

        Returns:
            Tuple with the transform name and its parameters dict.

        Raises:
            ValueError: If the mapping is malformed.
        """
        if not isinstance(transform, Mapping):
            raise ValueError("Cada transformação deve ser um mapeamento YAML.")
        name = transform.get("name")
        params = transform.get("params", {})
        if not isinstance(name, str) or not isinstance(params, Mapping):
            raise ValueError("Transformação YAML requer 'name' e 'params' válidos.")
        return name, dict(params)

    @staticmethod
    def _has_required_columns(df: pd.DataFrame, name: str) -> bool:
        """Check that a transform's required source columns are present.

        Args:
            df: DataFrame to inspect.
            name: Transform name.

        Returns:
            True if all required columns exist, otherwise False.
        """
        required_columns = {
            "bid_ask_spread": {"bid_price", "ask_price"},
            "order_imbalance": {"bid_qty", "ask_qty"},
        }
        return required_columns.get(name, set()).issubset(df.columns)

    @staticmethod
    def _add_feature_columns(
        df: pd.DataFrame,
        name: str,
        params: Mapping[str, Any],
        values: pd.Series | tuple[pd.Series, ...],
    ) -> None:
        """Add the computed feature values to the DataFrame under the right columns.

        Args:
            df: DataFrame to mutate in place with the new feature columns.
            name: Transform name.
            params: Transform parameters used to derive column names.
            values: Computed Series or tuple of Series from the transform.
        """
        column = params.get("column")
        period = params.get("period")
        if name == "bollinger":
            upper, middle, lower = values
            df["bb_upper"] = upper
            df["bb_middle"] = middle
            df["bb_lower"] = lower
        elif name == "avg_price_deviation":
            df[f"avg_price_deviation_sma{period}"] = values
        elif name == "change_percent":
            df["price_change_percent" if column == "close" else "volume_change_24h"] = (
                values
            )
        elif name == "sma" and column == "volume":
            df[f"volume_sma_{period}"] = values
        elif period is not None:
            df[f"{name}_{period}"] = values
        else:
            df[name] = values
