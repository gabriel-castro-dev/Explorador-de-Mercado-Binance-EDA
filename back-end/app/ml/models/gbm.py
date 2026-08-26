"""LightGBM global multi-símbolo: um regressor por horizonte, símbolo categórico.

Determinismo é requisito de publicação (mesma seed ⇒ mesmas previsões), então o
treino roda single-thread com ``deterministic=True`` — o dataset diário é pequeno
o bastante para isso custar segundos, não minutos.
"""

import pandas as pd
from lightgbm import LGBMRegressor

_DEFAULT_PARAMS = {
    "n_estimators": 400,
    "learning_rate": 0.05,
    "num_leaves": 31,
    "min_child_samples": 20,
    "subsample": 0.9,
    "subsample_freq": 1,
    "colsample_bytree": 0.9,
    "reg_lambda": 1.0,
}

_SYMBOL_FEATURE = "symbol_id"


class LightGBMModel:
    """Segue o protocolo dos modelos do projeto (fit/predict, ver baselines.py)."""

    def __init__(self, seed: int = 42, params: dict | None = None):
        self.seed = seed
        self.params = {**_DEFAULT_PARAMS, **(params or {})}

    def fit(
        self,
        train_frame: pd.DataFrame,
        feature_columns: tuple[str, ...],
        target_columns: tuple[str, ...],
    ) -> "LightGBMModel":
        self.feature_columns = tuple(feature_columns)
        self.target_columns = tuple(target_columns)
        # Categorias fixadas no treino: símbolo fora delas vira NaN no predict e
        # o LightGBM trata como categoria ausente — sem crash, sem chute mudo.
        self.symbol_dtype = pd.CategoricalDtype(sorted(train_frame["symbol"].unique()))
        design = self._design_matrix(train_frame)
        self.models: dict[str, LGBMRegressor] = {}
        for target in target_columns:
            model = LGBMRegressor(
                random_state=self.seed,
                n_jobs=1,
                deterministic=True,
                verbose=-1,
                **self.params,
            )
            model.fit(design, train_frame[target].to_numpy())
            self.models[target] = model
        return self

    def predict(self, frame: pd.DataFrame) -> pd.DataFrame:
        design = self._design_matrix(frame)
        predictions = {
            target: self.models[target].predict(design) for target in self.target_columns
        }
        return pd.DataFrame(predictions, index=frame.index)[list(self.target_columns)]

    def feature_importance(self) -> pd.Series:
        """Importância média (gain) entre horizontes — interpretabilidade mínima."""
        frames = []
        for target, model in self.models.items():
            booster = model.booster_
            frames.append(
                pd.Series(
                    booster.feature_importance(importance_type="gain"),
                    index=booster.feature_name(),
                    name=target,
                )
            )
        return pd.concat(frames, axis=1).mean(axis=1).sort_values(ascending=False)

    def _design_matrix(self, frame: pd.DataFrame) -> pd.DataFrame:
        design = frame[list(self.feature_columns)].copy()
        # Códigos explícitos: símbolo fora das categorias do treino vira -1
        # (categoria ausente para o LightGBM), sem cast deprecado do pandas.
        categories = self.symbol_dtype.categories
        codes = categories.get_indexer(frame["symbol"])
        design[_SYMBOL_FEATURE] = pd.Categorical.from_codes(codes, categories=categories)
        return design
