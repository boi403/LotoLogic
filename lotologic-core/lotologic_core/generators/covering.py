"""
Greedy Covering Design — gera o número mínimo (heurístico) de bilhetes que,
dado um pool de N dezenas, garante uma faixa de acerto se K delas saírem.

Implementa o módulo "Desdobramento" descrito no README do LotoLogic.

PROBLEMA FORMAL — Covering Design C(v, k, t):
    Dado um conjunto V de tamanho v, encontrar o menor número de blocos
    de tamanho k tal que todo subconjunto de tamanho t de V esteja
    contido em pelo menos um bloco.

NO LOTOLOGIC:
    v = pool escolhido pelo usuário (ex: 10 dezenas favoritas)
    k = tamanho do bilhete (ex: 6 para Mega-Sena)
    t = nível de garantia (ex: 4 para "garantir uma quadra se 4 saírem")

ENCONTRAR O ÓTIMO É NP-DIFÍCIL. Usamos heurística gulosa: a cada passo
escolhemos o bilhete que cobre mais tuplas-t ainda descobertas.

Não pretendemos competir com bibliotecas especializadas (combinatorial
design tables) — para os tamanhos de pool razoáveis em loteria
(N ≤ 20), o greedy gera resultados na mesma ordem de magnitude da
solução ótima e roda em < 1 segundo.
"""

from __future__ import annotations

from itertools import combinations
from typing import Optional

import numpy as np


def greedy_covering(
    pool: tuple[int, ...],
    block_size: int,
    guarantee: int,
    rng: Optional[np.random.Generator] = None,
) -> list[tuple[int, ...]]:
    """
    Gera blocos (bilhetes) que cobrem todas as tuplas de tamanho `guarantee`
    do `pool`.

    Args:
        pool: dezenas escolhidas pelo usuário.
        block_size: tamanho de cada bilhete (k).
        guarantee: tamanho da garantia (t). Ex: 4 = "garante quadra se 4
                   das minhas dezenas saírem".

    Returns:
        Lista de tuplas ordenadas, sem repetição entre blocos.

    Raises:
        ValueError: se parâmetros forem incoerentes.
    """
    if guarantee < 2:
        raise ValueError("guarantee deve ser >= 2 para fazer sentido")
    if block_size < guarantee:
        raise ValueError("block_size precisa ser >= guarantee")
    if len(pool) < block_size:
        raise ValueError("pool precisa ter pelo menos block_size dezenas")
    if len(set(pool)) != len(pool):
        raise ValueError("pool tem dezenas repetidas")

    rng = rng or np.random.default_rng()
    pool_sorted = tuple(sorted(pool))

    # Conjunto de todas as tuplas-t a cobrir, representadas como frozensets.
    uncovered: set[frozenset[int]] = {
        frozenset(c) for c in combinations(pool_sorted, guarantee)
    }
    blocks: list[tuple[int, ...]] = []

    while uncovered:
        best_block: Optional[tuple[int, ...]] = None
        best_covered = -1

        # Geramos vários blocos candidatos e escolhemos o que cobre mais.
        # Estratégia: priorizamos blocos que "concentrem" tuplas descobertas.
        # Para isso, contamos quantas dezenas de cada tupla descoberta cada
        # candidato carrega.
        candidates = _generate_candidates(pool_sorted, block_size, uncovered, rng)
        for candidate in candidates:
            covered = _count_covered(candidate, uncovered, guarantee)
            if covered > best_covered:
                best_covered = covered
                best_block = candidate
                if covered == _max_possible_coverage(block_size, guarantee, uncovered):
                    break  # não dá pra fazer melhor neste passo

        if best_block is None or best_covered == 0:
            # Falha de progresso (não deveria ocorrer com candidatos suficientes):
            # adiciona um bloco aleatório para evitar loop infinito.
            best_block = tuple(sorted(rng.choice(pool_sorted, block_size, replace=False)))
            best_covered = _count_covered(best_block, uncovered, guarantee)

        blocks.append(best_block)
        # Remove tuplas cobertas.
        for tup in list(uncovered):
            if tup.issubset(best_block):
                uncovered.discard(tup)

    return blocks


def _max_possible_coverage(block_size: int, guarantee: int, uncovered_set) -> int:
    """C(block_size, guarantee) = limite teórico de tuplas-t por bloco."""
    from math import comb

    return min(comb(block_size, guarantee), len(uncovered_set))


def _count_covered(
    block: tuple[int, ...], uncovered: set[frozenset[int]], guarantee: int
) -> int:
    """Quantas tuplas descobertas estão contidas no bloco."""
    block_set = frozenset(block)
    if guarantee > len(block_set):
        return 0
    count = 0
    # Otimização: enumeramos as combinações DO BLOCO e checamos se elas
    # estão no conjunto uncovered. Mais barato que iterar uncovered todo.
    for combo in combinations(block_set, guarantee):
        if frozenset(combo) in uncovered:
            count += 1
    return count


def _generate_candidates(
    pool: tuple[int, ...],
    block_size: int,
    uncovered: set[frozenset[int]],
    rng: np.random.Generator,
    n_candidates: int = 50,
) -> list[tuple[int, ...]]:
    """
    Gera blocos candidatos. Estratégia:
      1. Pegamos uma tupla descoberta aleatória.
      2. Construímos um bloco que a contém + dezenas extras escolhidas
         de forma a cobrir mais tuplas descobertas (preferência por
         dezenas que aparecem em muitas tuplas descobertas).
    """
    if not uncovered:
        return []

    candidates: list[tuple[int, ...]] = []
    pool_arr = np.array(pool)

    # Frequência de cada dezena nas tuplas descobertas (heurística de "valor").
    freq: dict[int, int] = {n: 0 for n in pool}
    for tup in uncovered:
        for n in tup:
            freq[n] = freq.get(n, 0) + 1

    uncovered_list = list(uncovered)

    for _ in range(n_candidates):
        # Pega um seed aleatório das tuplas descobertas para garantir progresso.
        seed_tup = uncovered_list[rng.integers(0, len(uncovered_list))]
        block_set = set(seed_tup)
        # Completa com dezenas com maior valor (preferência) + jitter aleatório.
        remaining = [n for n in pool if n not in block_set]
        # Ordena por valor (descendente) com pequeno ruído para diversificar.
        scored = [(freq[n] + rng.random(), n) for n in remaining]
        scored.sort(reverse=True)
        for _, n in scored:
            if len(block_set) >= block_size:
                break
            block_set.add(n)
        candidates.append(tuple(sorted(block_set)))

    # Remove duplicados.
    return list({tuple(c) for c in candidates})
