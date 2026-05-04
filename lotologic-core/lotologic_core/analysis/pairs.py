"""
Co-ocorrência de pares de dezenas.

Implementa o módulo "Pares" do SuperLab e a estratégia "Afinidade Histórica"
do Gerador, ambos descritos no README do LotoLogic. Em vez de loops Python,
usamos produto matricial — tornando viável calcular pares sobre 23k+
concursos sem segurar o app.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np

from ..domain.lottery import Draw, GameSpec
from .frequency import _draws_to_matrix


def cooccurrence_matrix(draws: Sequence[Draw], spec: GameSpec) -> np.ndarray:
    """
    Matriz quadrada (universe, universe) onde M[i, j] é o número de
    concursos em que as dezenas i+1 e j+1 saíram juntas.

    Diagonal contém a frequência absoluta de cada dezena.
    """
    matrix = _draws_to_matrix(draws, spec).astype(np.int64)
    if matrix.shape[0] == 0:
        return np.zeros((spec.universe, spec.universe), dtype=np.int64)
    # m.T @ m é a forma vetorizada padrão para co-ocorrência.
    return matrix.T @ matrix


def top_pairs(
    cooc: np.ndarray, k: int = 20, descending: bool = True
) -> list[tuple[int, int, int]]:
    """
    Top-K pares mais (ou menos) frequentes.
    Retorna [(dezena_a, dezena_b, contagem), ...] com a < b.
    """
    universe = cooc.shape[0]
    pairs: list[tuple[int, int, int]] = []
    # Apenas triângulo superior — evita pares duplicados (a,b) e (b,a)
    # e a diagonal (que é frequência simples, não par).
    iu = np.triu_indices(universe, k=1)
    counts = cooc[iu]
    order = np.argsort(-counts if descending else counts, kind="stable")[:k]
    for o in order:
        i, j = int(iu[0][o]), int(iu[1][o])
        pairs.append((i + 1, j + 1, int(counts[o])))
    return pairs


def affinity_score(
    candidate: tuple[int, ...],
    cooc: np.ndarray,
) -> float:
    """
    Score de afinidade de um bilhete: soma das co-ocorrências de todos os
    pares de dezenas do bilhete.

    É a métrica usada pela estratégia "Afinidade Histórica" do Gerador
    e como objetivo no otimizador Pareto do SuperLab. Quanto maior,
    mais "historicamente compatíveis" são as dezenas escolhidas.

    Versão vetorizada: usa fancy indexing pra extrair a submatriz e
    soma o triângulo superior.
    """
    if len(candidate) < 2:
        return 0.0
    idx = np.array([n - 1 for n in candidate], dtype=np.intp)
    sub = cooc[np.ix_(idx, idx)]
    # np.triu(k=1) zera diagonal e triângulo inferior.
    return float(np.triu(sub, k=1).sum())


def normalized_affinity(
    candidate: tuple[int, ...],
    cooc: np.ndarray,
) -> float:
    """
    Afinidade dividida pelo número de pares possíveis e pela média
    histórica — devolve um valor próximo a 1.0 quando o bilhete tem
    pares "típicos" e >> 1.0 quando tem pares incomumente frequentes.

    Útil pro X-Ray porque dá interpretação intuitiva sem o usuário
    precisar saber a escala bruta.
    """
    n = len(candidate)
    if n < 2:
        return 0.0
    raw = affinity_score(candidate, cooc)

    # Média histórica: total de co-ocorrências / total de pares possíveis no
    # universo. Esse é o valor esperado se as dezenas fossem aleatórias.
    universe = cooc.shape[0]
    total_pairs_universe = universe * (universe - 1) // 2
    total_cooc = float(np.triu(cooc, k=1).sum())
    expected_per_pair = total_cooc / total_pairs_universe if total_pairs_universe else 0.0
    pairs_in_ticket = n * (n - 1) // 2
    expected_total = expected_per_pair * pairs_in_ticket
    return raw / expected_total if expected_total > 0 else 0.0
