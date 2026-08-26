"""Monte Carlo (fase 1): bootstrap dos resíduos de validação sobre o drift previsto.

Trajetórias são dados, não artefatos (ADR-0004): o job simula, grava em
``monte_carlo_runs`` e a API só lê. Coerência com a banda de incerteza vem de
construção — a banda são os quantis 10/90 dos MESMOS resíduos que alimentam a
simulação, então a faixa 10–90 % da nuvem reproduz ``pred_lower``/``pred_upper``.

Cada trajetória reamostra UMA linha de validação inteira (resíduo de h=1..H da
mesma origem), preservando a forma de trajetórias reais em vez de sortear um
erro independente por passo. Determinismo: seed derivada de ``model_version``.
"""

import zlib

import numpy as np
import pandas as pd


def seed_from_version(model_version: str) -> int:
    """Seed estável (CRC32) por versão: mesma rodada → mesma nuvem."""
    return zlib.crc32(model_version.encode("utf-8"))


def validation_residuals(
    frame: pd.DataFrame, predictions: pd.DataFrame, targets: tuple[str, ...]
) -> np.ndarray:
    """Matriz (n_linhas × n_horizontes) de ``y_h − ŷ_h`` na validação."""
    return np.column_stack(
        [frame[target].to_numpy() - predictions[target].to_numpy() for target in targets]
    )


def simulate_paths(
    close: float,
    predicted_log_returns: np.ndarray,
    residuals: np.ndarray,
    n_paths: int,
    seed: int,
) -> np.ndarray:
    """Preços simulados (``n_paths × H``): ``close × exp(ŷ_h + resíduo_h)``.

    ``residuals`` tem uma linha por cenário de validação e uma coluna por
    horizonte; cada trajetória sorteia uma linha inteira com reposição.
    """
    predicted = np.asarray(predicted_log_returns, dtype=float)
    residuals = np.asarray(residuals, dtype=float)
    if residuals.ndim != 2 or residuals.shape[1] != predicted.shape[0]:
        raise ValueError(
            f"residuals deve ter forma (n, {predicted.shape[0]}); recebido {residuals.shape}."
        )
    if residuals.shape[0] == 0:
        raise ValueError("Sem resíduos de validação para simular.")
    if n_paths <= 0:
        raise ValueError("n_paths deve ser positivo.")
    rng = np.random.default_rng(seed)
    scenarios = rng.integers(0, residuals.shape[0], size=n_paths)
    log_paths = predicted[np.newaxis, :] + residuals[scenarios]
    return float(close) * np.exp(log_paths)


def classify_paths(paths: np.ndarray) -> dict[str, int]:
    """Índices ``best``/``worst`` (maior/menor terminal) e ``base`` (mais perto da mediana)."""
    terminal = np.asarray(paths)[:, -1]
    median = float(np.median(terminal))
    return {
        "best": int(np.argmax(terminal)),
        "base": int(np.argmin(np.abs(terminal - median))),
        "worst": int(np.argmin(terminal)),
    }
