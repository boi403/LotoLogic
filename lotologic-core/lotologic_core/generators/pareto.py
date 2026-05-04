"""
Otimizador Pareto multi-objetivo para portfólios de bilhetes.

Implementa o módulo "Otimizar (Multi-objetivo)" do SuperLab descrito no
README do LotoLogic — gera portfólios balanceando três objetivos:

    1. Frequência histórica (média da relativa das dezenas de cada bilhete)
    2. Diversidade Jaccard (média 1 - Jaccard entre cada par de bilhetes)
    3. Cobertura de pares (proporção dos pares possíveis no pool cobertos)

Quanto mais alto cada objetivo, melhor. O usuário define pesos via sliders;
nós resolvemos por scalarização linear (soma ponderada). É a abordagem
mais simples e produz toda a frente Pareto convexa — adequada para
portfólios pequenos (< 50 bilhetes), que é o limite prático do app.

Para problemas maiores valeria substituir por NSGA-II, mas adicionaria
complexidade desproporcional ao ganho aqui.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from ..analysis.frequency import FrequencyStats
from ..domain.lottery import GameSpec
from .strategies import generate_with_strategy, sample_from_scores, scores_balanced


@dataclass
class ParetoConfig:
    """Pesos dos três objetivos. Devem somar 1 (são normalizados se não)."""

    weight_frequency: float = 1.0
    weight_diversity: float = 1.0
    weight_pair_coverage: float = 1.0
    n_candidates: int = 200  # quantos portfólios sortear antes de escolher o melhor
    seed: Optional[int] = None


@dataclass
class ParetoResult:
    portfolio: list[tuple[int, ...]]
    score: float
    components: dict[str, float]


def _frequency_score(
    portfolio: list[tuple[int, ...]], stats: FrequencyStats
) -> float:
    """Média das frequências relativas das dezenas escolhidas."""
    if stats.total_contests == 0 or not portfolio:
        return 0.0
    all_idx = np.array(
        [n - 1 for ticket in portfolio for n in ticket], dtype=np.intp
    )
    return float(stats.relative[all_idx].mean())


def _diversity_score(portfolio: list[tuple[int, ...]]) -> float:
    """
    Média de (1 - Jaccard) entre todos os pares de bilhetes.
    Score em [0,1] — 1 = bilhetes totalmente disjuntos.
    """
    if len(portfolio) < 2:
        return 1.0
    sets = [set(t) for t in portfolio]
    n = len(sets)
    distances = []
    for i in range(n):
        for j in range(i + 1, n):
            inter = len(sets[i] & sets[j])
            union = len(sets[i] | sets[j])
            jaccard = inter / union if union else 0.0
            distances.append(1.0 - jaccard)
    return float(np.mean(distances))


def _pair_coverage_score(
    portfolio: list[tuple[int, ...]], spec: GameSpec
) -> float:
    """
    Proporção dos pares possíveis (no universo) cobertos pelo portfólio.

    Score em [0,1]. Para portfólios pequenos será baixo, mas o que importa
    é o ranking relativo entre candidatos.
    """
    universe = spec.universe
    total_pairs = universe * (universe - 1) // 2
    if total_pairs == 0 or not portfolio:
        return 0.0
    covered: set[tuple[int, int]] = set()
    for ticket in portfolio:
        sorted_t = sorted(ticket)
        for i in range(len(sorted_t)):
            for j in range(i + 1, len(sorted_t)):
                covered.add((sorted_t[i], sorted_t[j]))
    return len(covered) / total_pairs


def optimize_portfolio(
    spec: GameSpec,
    stats: FrequencyStats,
    portfolio_size: int,
    n_numbers_per_ticket: int,
    config: Optional[ParetoConfig] = None,
    cooc: Optional[np.ndarray] = None,
) -> ParetoResult:
    """
    Gera `n_candidates` portfólios usando estratégia "balanced" e devolve
    o que maximiza a soma ponderada dos três objetivos.

    Não fazemos NSGA porque o usuário pediu UMA solução; a soma ponderada
    é a forma mais direta de respeitar o controle por sliders.
    """
    cfg = config or ParetoConfig()
    rng = np.random.default_rng(cfg.seed)

    # Normaliza pesos para somarem 1 — isso mantém a comparação justa
    # mesmo se o usuário passar valores arbitrários.
    w_total = cfg.weight_frequency + cfg.weight_diversity + cfg.weight_pair_coverage
    if w_total <= 0:
        raise ValueError("Pelo menos um peso deve ser positivo")
    wf = cfg.weight_frequency / w_total
    wd = cfg.weight_diversity / w_total
    wp = cfg.weight_pair_coverage / w_total

    base_scores = scores_balanced(spec, stats)

    best_portfolio: Optional[list[tuple[int, ...]]] = None
    best_score = -1.0
    best_components: dict[str, float] = {}

    for _ in range(cfg.n_candidates):
        # Cada portfólio: sorteamos com perturbação dos scores base, para
        # gerar variação real entre os bilhetes.
        portfolio: list[tuple[int, ...]] = []
        seen: set[tuple[int, ...]] = set()
        attempts = 0
        max_attempts = portfolio_size * 5
        while len(portfolio) < portfolio_size and attempts < max_attempts:
            jitter = rng.uniform(0.5, 1.5, size=len(base_scores))
            perturbed = base_scores * jitter
            ticket = sample_from_scores(perturbed, n_numbers_per_ticket, rng)
            attempts += 1
            if ticket in seen:
                continue
            seen.add(ticket)
            portfolio.append(ticket)

        if len(portfolio) < portfolio_size:
            # universo pequeno demais para ter `portfolio_size` bilhetes únicos
            continue

        f = _frequency_score(portfolio, stats)
        d = _diversity_score(portfolio)
        p = _pair_coverage_score(portfolio, spec)
        score = wf * f + wd * d + wp * p

        if score > best_score:
            best_score = score
            best_portfolio = portfolio
            best_components = {
                "frequency": f,
                "diversity": d,
                "pair_coverage": p,
                "weighted": score,
            }

    if best_portfolio is None:
        raise RuntimeError("Falhou em gerar portfólio único — pool muito restrito")

    return ParetoResult(
        portfolio=best_portfolio,
        score=best_score,
        components=best_components,
    )
