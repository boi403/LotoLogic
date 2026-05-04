"""
As 7 estratégias do módulo Gerador descritas no README do LotoLogic.

Cada estratégia é uma função que recebe `(spec, stats, cooc, n_numbers, rng)`
e devolve uma tupla de dezenas. O design funcional facilita compor
estratégias e testá-las isoladamente.

Equivalente ao "Modo Combinado" / "Modo Ponderado" do Logic Pro: cada
estratégia produz um vetor de scores por dezena, e o seletor pesado
escolhe `n_numbers` sem reposição, com probabilidade proporcional ao score.
"""

from __future__ import annotations

from typing import Callable, Optional

import numpy as np

from ..domain.lottery import GameSpec
from ..analysis.frequency import FrequencyStats


# ---------------------------------------------------------------------------
# Núcleo: cada estratégia gera um vetor de pesos (scores por dezena).
# ---------------------------------------------------------------------------

ScoreVector = np.ndarray  # shape (universe,)


def _normalize(scores: ScoreVector) -> ScoreVector:
    """Garante scores não-negativos e com pelo menos um valor positivo."""
    scores = np.asarray(scores, dtype=np.float64)
    scores = np.maximum(scores, 0)  # sem negativos — quebraria a roleta
    if scores.sum() == 0:
        # Fallback uniforme se todos os pesos zerarem.
        scores = np.ones_like(scores)
    return scores


def scores_random(spec: GameSpec, *_args, **_kw) -> ScoreVector:
    """Aleatório puro — todos os pesos iguais."""
    return np.ones(spec.universe, dtype=np.float64)


def scores_historical_frequency(
    spec: GameSpec, stats: FrequencyStats, *_args, **_kw
) -> ScoreVector:
    """Frequência absoluta histórica."""
    if stats.total_contests == 0:
        return scores_random(spec)
    return _normalize(stats.absolute.copy())


def scores_recent_frequency(
    spec: GameSpec, stats: FrequencyStats, *_args, **_kw
) -> ScoreVector:
    """Frequência ponderada por recência. `stats` deve ser de janela curta."""
    if stats.total_contests == 0:
        return scores_random(spec)
    return _normalize(stats.recency_weighted.copy())


def scores_delayed(
    spec: GameSpec, stats: FrequencyStats, *_args, **_kw
) -> ScoreVector:
    """Atraso atual — quanto maior, mais peso."""
    if stats.total_contests == 0:
        return scores_random(spec)
    return _normalize(stats.delays.astype(np.float64))


def scores_balanced(
    spec: GameSpec, stats: FrequencyStats, *_args, **_kw
) -> ScoreVector:
    """
    Mistura 50/50 entre frequência e atraso, ambos normalizados em [0,1].
    Evita que uma escala domine a outra (atrasos podem ser muito > absolute).
    """
    if stats.total_contests == 0:
        return scores_random(spec)
    freq_norm = stats.absolute / max(stats.absolute.max(), 1)
    delay_norm = stats.delays / max(stats.delays.max(), 1)
    return _normalize(0.5 * freq_norm + 0.5 * delay_norm)


def scores_hybrid(
    spec: GameSpec,
    stats: FrequencyStats,
    *_args,
    weights: Optional[dict[str, float]] = None,
    **_kw,
) -> ScoreVector:
    """
    Combinação ponderada — o "Modo Ponderado" do Logic Pro.
    `weights` mapeia 'historical', 'recent', 'delay'. Faltantes ficam em 0.
    """
    if stats.total_contests == 0:
        return scores_random(spec)
    w = {"historical": 1.0, "recent": 1.0, "delay": 1.0, **(weights or {})}
    hist = stats.absolute / max(stats.absolute.max(), 1)
    rec = stats.recency_weighted / max(stats.recency_weighted.max(), 1)
    delay = stats.delays / max(stats.delays.max(), 1)
    combined = w["historical"] * hist + w["recent"] * rec + w["delay"] * delay
    return _normalize(combined)


def scores_affinity(
    spec: GameSpec,
    stats: FrequencyStats,
    cooc: Optional[np.ndarray] = None,
    *_args,
    **_kw,
) -> ScoreVector:
    """
    Afinidade histórica — usa a co-ocorrência total de cada dezena (soma
    da linha da matriz, excluindo diagonal). Dezenas que aparecem com mais
    "amigas" recebem peso maior.
    """
    if cooc is None or stats.total_contests == 0:
        return scores_random(spec)
    affinity = cooc.sum(axis=1) - np.diag(cooc)  # soma sem a auto-cooc
    return _normalize(affinity.astype(np.float64))


# ---------------------------------------------------------------------------
# Registry — corresponde 1:1 às 7 estratégias do README.
# ---------------------------------------------------------------------------

StrategyFn = Callable[..., ScoreVector]

STRATEGIES: dict[str, StrategyFn] = {
    "random": scores_random,
    "historical": scores_historical_frequency,
    "recent": scores_recent_frequency,
    "delayed": scores_delayed,
    "balanced": scores_balanced,
    "hybrid": scores_hybrid,
    "affinity": scores_affinity,
}

# Aliases em PT-BR para casar com o app:
STRATEGY_ALIASES = {
    "Aleatório Puro": "random",
    "Frequência Histórica": "historical",
    "Frequência Recente": "recent",
    "Dezenas Atrasadas": "delayed",
    "Balanceado": "balanced",
    "Híbrido": "hybrid",
    "Afinidade Histórica": "affinity",
}


# ---------------------------------------------------------------------------
# Sampler: dados scores, escolhe `n` dezenas sem reposição.
# ---------------------------------------------------------------------------


def sample_from_scores(
    scores: ScoreVector,
    n_numbers: int,
    rng: np.random.Generator,
) -> tuple[int, ...]:
    """
    Sorteio sem reposição com probabilidade proporcional ao score.

    Implementação via "weighted reservoir sampling" (Efraimidis-Spirakis):
    para cada item i, gera uma chave `u_i^(1/w_i)` e pega os `n` maiores.
    Robusto a pesos com escalas muito diferentes.
    """
    weights = _normalize(scores)
    # Para evitar log(0): adiciona piso ínfimo. Não muda o ranking.
    weights = weights + 1e-12
    u = rng.random(len(weights))
    keys = np.log(u) / weights  # equivalente a u^(1/w) sem overflow
    chosen = np.argsort(keys)[-n_numbers:]
    return tuple(sorted(int(i + 1) for i in chosen))


def generate_with_strategy(
    strategy: str,
    spec: GameSpec,
    stats: FrequencyStats,
    n_numbers: int,
    cooc: Optional[np.ndarray] = None,
    weights: Optional[dict[str, float]] = None,
    rng: Optional[np.random.Generator] = None,
) -> tuple[int, ...]:
    """
    Atalho: gera um bilhete usando uma das 7 estratégias.
    Aceita o nome inglês (`random`, `delayed`, ...) ou o PT-BR do app.
    """
    strategy_key = STRATEGY_ALIASES.get(strategy, strategy)
    if strategy_key not in STRATEGIES:
        raise ValueError(
            f"Estratégia '{strategy}' desconhecida. "
            f"Disponíveis: {list(STRATEGIES.keys())}"
        )
    if not (spec.min_picks <= n_numbers <= spec.max_picks):
        raise ValueError(
            f"n_numbers={n_numbers} fora do permitido "
            f"[{spec.min_picks}, {spec.max_picks}] para {spec.name}"
        )

    rng = rng or np.random.default_rng()
    fn = STRATEGIES[strategy_key]
    scores = fn(spec, stats, cooc, weights=weights)
    return sample_from_scores(scores, n_numbers, rng)
