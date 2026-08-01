from typing import Callable, Dict

from transforms.technical_indicators import TechnicalIndicatorsTransform


class TransformRegistry:
    def __init__(self):
        self._transforms: Dict[str, Callable] = {
            "sma": TechnicalIndicatorsTransform.calculate_sma,
            "ema": TechnicalIndicatorsTransform.calculate_ema,
            "rsi": TechnicalIndicatorsTransform.calculate_rsi,
            "bollinger": TechnicalIndicatorsTransform.calculate_bollinger_bands,
            "avg_price_deviation": TechnicalIndicatorsTransform.calculate_avg_price_deviation,
            "atr": TechnicalIndicatorsTransform.calculate_atr,
            "price_change_percent": TechnicalIndicatorsTransform.calculate_change_percent,
            "volume_change_percent": TechnicalIndicatorsTransform.calculate_change_percent,
        }

    def get(self, name: str) -> Callable:
        """Retrive a transformation function by name."""

        transform_fn = self._transforms.get(name.lower())
        if not transform_fn:
            raise KeyError(
                f"Transformação '{name}' não encontrada. "
                f"Opções disponíveis: {list(self._transforms.keys())}"
            )
        return transform_fn

    def register(self, name: str, func: Callable):
        """Register a new transformation function."""

        self._transforms[name.lower()] = func


registry = TransformRegistry()
