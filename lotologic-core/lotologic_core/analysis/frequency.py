"""
Análise estatística de frequência, atraso e recência.

Substitui o `criadorTabelaFreq` hard-coded do AG-LotofacilPreditor
(que tinha 10 sorteios manualmente digitados no código!) por uma
implementação vetorizada que aceita qualquer histórico real.

Implementa:
  - Frequência absoluta e relativa por dezena
  - Atraso (sorteios desde a última aparição) — dezenas "frias"
  - Recência com decaimento exponencial — pondera mais os concursos recentes
  - Análise por janela (últimos N concursos) — corresponde ao seletor de
    período do Dashboard do LotoLogic
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from ..domain.lottery import Draw, GameSpec


@dataclass(frozen=True)
class FrequencyStats:
    """
    Estatísticas pré-computadas para uma loteria.

    Todos os arrays são indexados de 0 a universe-1, onde índice `i`
    corresponde à dezena `i+1` (convenção: a dezena 1 vai no índice 0).

    Manter como ndarray permite que o motor de fitness do AG e o
    quality_score consumam direto, sem reconverter — ganho real de
    performance no benchmark de gerar 10k jogos.
    """

    spec: GameSpec
    total_contests: int
    absolute: np.ndarray  # shape (universe,) — quantas vezes cada dezena saiu
    relative: np.ndarray  # absolute / total_contests
    delays: np.ndarray  # sorteios desde a última aparição (atraso atual)
    last_seen: np.ndarray  # número do último concurso em que cada dezena saiu (-1 se nunca)
    recency_weighted: np.ndarray  # frequência ponderada por decaimento exponencial


def _draws_to_matrix(draws: Sequence[Draw], spec: GameSpec) -> np.ndarray:
    """
    Converte uma sequência de Draws numa matriz binária (n_contests, universe).
    matriz[i, j] = 1 sse a dezena `j+1` saiu no concurso `i`.

    Vetorizar dessa forma é o que torna todo o resto barato.
    """
    if not draws:
        return np.zeros((0, spec.universe), dtype=np.int8)

    n = len(draws)
    matrix = np.zeros((n, spec.universe), dtype=np.int8)
    for i, draw in enumerate(draws):
        # Lotomania trata 100 como dezena "0" mas usamos 100 internamente.
        idxs = [num - 1 for num in draw.numbers if 1 <= num <= spec.universe]
        matrix[i, idxs] = 1
    return matrix


def compute_frequency_stats(
    draws: Sequence[Draw],
    spec: GameSpec,
    recency_half_life: int = 50,
) -> FrequencyStats:
    """
    Calcula todas as estatísticas de uma vez.

    `recency_half_life`: número de concursos para o peso decair pela metade.
    Default 50 é compatível com o "últimos 50 concursos" do Dashboard.
    Use 20 para o foco "Frequência Recente" do gerador, 200+ para uma
    visão de longo prazo.
    """
    if not draws:
        # Histórico vazio é caso degenerado — retornamos zeros sem dividir por zero.
        zeros = np.zeros(spec.universe, dtype=np.float64)
        return FrequencyStats(
            spec=spec,
            total_contests=0,
            absolute=zeros.copy(),
            relative=zeros.copy(),
            delays=np.full(spec.universe, -1, dtype=np.int64),
            last_seen=np.full(spec.universe, -1, dtype=np.int64),
            recency_weighted=zeros.copy(),
        )

    # Os concursos vêm em qualquer ordem; ordenamos por número para que
    # "atraso" e "recência" façam sentido temporal.
    sorted_draws = sorted(draws, key=lambda d: d.contest)
    matrix = _draws_to_matrix(sorted_draws, spec)
    n_contests = matrix.shape[0]

    absolute = matrix.sum(axis=0).astype(np.float64)
    relative = absolute / n_contests

    # last_seen: índice (na sequência ordenada) do último concurso onde cada
    # dezena apareceu. Argmax na matriz invertida = primeira ocorrência de
    # baixo para cima = última de cima para baixo.
    last_seen_idx = np.where(
        matrix.any(axis=0),
        n_contests - 1 - matrix[::-1].argmax(axis=0),
        -1,
    )

    # delays: quantos concursos ATRÁS está a última aparição.
    delays = np.where(last_seen_idx >= 0, n_contests - 1 - last_seen_idx, n_contests)

    # last_seen como número de concurso (não índice) — útil para exibição.
    contest_numbers = np.array([d.contest for d in sorted_draws])
    last_seen_contest = np.where(last_seen_idx >= 0, contest_numbers[last_seen_idx], -1)

    # Recência: aplicamos decaimento exponencial nos pesos por linha.
    # Concurso mais recente = peso 1; concurso há `half_life` atrás = peso 0.5.
    decay = np.log(2) / max(recency_half_life, 1)
    weights = np.exp(-decay * np.arange(n_contests - 1, -1, -1, dtype=np.float64))
    weights /= weights.sum()  # normaliza para somar 1
    recency_weighted = matrix.T @ weights  # shape (universe,)

    return FrequencyStats(
        spec=spec,
        total_contests=n_contests,
        absolute=absolute,
        relative=relative,
        delays=delays,
        last_seen=last_seen_contest,
        recency_weighted=recency_weighted,
    )


def top_frequent(stats: FrequencyStats, k: int = 10) -> list[tuple[int, int]]:
    """Top-K dezenas mais frequentes. Retorna [(dezena, contagem), ...]."""
    order = np.argsort(-stats.absolute, kind="stable")[:k]
    return [(int(idx + 1), int(stats.absolute[idx])) for idx in order]


def top_delayed(stats: FrequencyStats, k: int = 10) -> list[tuple[int, int]]:
    """Top-K dezenas mais atrasadas. Retorna [(dezena, atraso), ...]."""
    order = np.argsort(-stats.delays, kind="stable")[:k]
    return [(int(idx + 1), int(stats.delays[idx])) for idx in order]


def window_stats(
    draws: Sequence[Draw],
    spec: GameSpec,
    window: int,
    recency_half_life: int = 50,
) -> FrequencyStats:
    """
    Estatísticas considerando apenas os últimos `window` concursos.

    Espelha o seletor de período (5/10/30/50/100) do Dashboard do LotoLogic.
    """
    if window <= 0:
        raise ValueError("window deve ser > 0")
    sorted_draws = sorted(draws, key=lambda d: d.contest)
    return compute_frequency_stats(sorted_draws[-window:], spec, recency_half_life)
