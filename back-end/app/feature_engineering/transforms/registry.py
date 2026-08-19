from collections.abc import Callable

from app.feature_engineering.transforms.technical_indicators import (
    TechnicalIndicatorsTransform,
)


class TransformRegistry:
    """Central catalog to resolve transformation functions by name.

    Maps string identifiers (e.g., 'sma') to the corresponding callable
    functions from TechnicalIndicatorsTransform.

    Attributes:
        _transforms: Mapping of transform names to callable functions.
    """

    def __init__(self) -> None:
        """Initialize the registry with the default transformation catalog."""
        self._transforms: dict[str, Callable] = {
            "sma": TechnicalIndicatorsTransform.calculate_sma,
            "ema": TechnicalIndicatorsTransform.calculate_ema,
            "rsi": TechnicalIndicatorsTransform.calculate_rsi,
            "bollinger": TechnicalIndicatorsTransform.calculate_bollinger_bands,
            "avg_price_deviation": TechnicalIndicatorsTransform.calculate_avg_price_deviation,
            "atr": TechnicalIndicatorsTransform.calculate_atr,
            "change_percent": TechnicalIndicatorsTransform.calculate_change_percent,
            "bid_ask_spread": TechnicalIndicatorsTransform.calculate_bid_ask_spread,
            "order_imbalance": TechnicalIndicatorsTransform.calculate_order_imbalance,
        }

    def get(self, name: str) -> Callable:
        """Retrieve a transformation function by name.

        Args:
            name: Registered transform name (case-insensitive).

        Returns:
            The callable transformation function.

        Raises:
            KeyError: If no transform is registered under the given name.
        """
        transform_function = self._transforms.get(name.lower())
        if transform_function is None:
            raise KeyError(
                f"Transformação '{name}' não encontrada. "
                f"Opções disponíveis: {list(self._transforms.keys())}"
            )
        return transform_function


registry = TransformRegistry()
