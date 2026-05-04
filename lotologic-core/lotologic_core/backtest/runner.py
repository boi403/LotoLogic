"""
Backtest de estratégias contra histórico real.

Implementa o módulo "Backtest" do SuperLab. A ideia: roda uma estratégia
N vezes contra os concursos passados e mede com que frequência teria
acertado cada faixa.

IMPORTANTE — sobre cuidado científico:
    O backtest pode dar a ilusão de que uma estratégia "funciona", mas
    loteria é Markoviana — cada concurso é independente. Se uma
    estratégia pareceu boa em backtest, isso é em geral overfitting.
    O propósito legítimo do backtest é VERIFICAR que a implementação
    não tem bugs (estratégias devem performar próximo do baseline
    aleatório ao longo prazo) e medir variância.

    O LotoLogic explicitamente avisa "Não prevê resultados futuros —
    nenhum software consegue isso" — mantemos esse rigor.

Implementação:
  - Rolling window: a cada concurso K, usa apenas os K-1 anteriores
    como histórico para evitar look-ahead.
  - Múltiplas amostras por concurso (config.tickets_per_contest) para
    reduzir ruído.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

import numpy as np

from ..analysis.frequency import compute_frequency_stats
from ..domain.lottery import Draw, GameSpec
from ..generators.strategies import generate_with_strategy


@dataclass
class BacktestConfig:
    strategy: str = "balanced"
    n_numbers: Optional[int] = None  # None = usa spec.min_picks
    tickets_per_contest: int = 10
    min_history: int = 50  # exige pelo menos N concursos antes de começar a testar
    seed: Optional[int] = None


@dataclass
class HitDistribution:
    """Distribuição de acertos: {n_hits: count}. Útil para visualizar."""

    counts: dict[int, int] = field(default_factory=dict)
    total_tickets: int = 0

    def add(self, hits: int) -> None:
        self.counts[hits] = self.counts.get(hits, 0) + 1
        self.total_tickets += 1

    def probability(self, n_hits: int) -> float:
        if self.total_tickets == 0:
            return 0.0
        return self.counts.get(n_hits, 0) / self.total_tickets


@dataclass
class BacktestResult:
    config: BacktestConfig
    distribution: HitDistribution
    contests_tested: int
    expected_hits_per_ticket: float
    """Média de acertos por bilhete — comparar com a média uniforme teórica
    (n_picked * draw_size / universe) é o sanity check."""


def run_backtest(
    spec: GameSpec,
    history: Sequence[Draw],
    config: Optional[BacktestConfig] = None,
) -> BacktestResult:
    """
    Roda backtest cronológico (sem look-ahead).

    Algoritmo:
      Para cada concurso C com índice >= min_history:
        - Calcula stats com history[:C]
        - Gera `tickets_per_contest` bilhetes pela estratégia
        - Conta acertos vs history[C].numbers

    O custo é O(n_contests * tickets * universe) — sub-segundo em
    máquinas modernas para os ~3000 concursos típicos.
    """
    cfg = config or BacktestConfig()
    sorted_history = sorted(history, key=lambda d: d.contest)
    n_picked = cfg.n_numbers or spec.min_picks
    rng = np.random.default_rng(cfg.seed)

    if len(sorted_history) <= cfg.min_history:
        raise ValueError(
            f"Histórico curto ({len(sorted_history)}) — precisa de mais que "
            f"min_history={cfg.min_history} concursos"
        )

    distribution = HitDistribution()
    total_hits = 0
    contests_tested = 0

    for i in range(cfg.min_history, len(sorted_history)):
        past = sorted_history[:i]
        target_set = set(sorted_history[i].numbers)
        stats = compute_frequency_stats(past, spec)
        # cooc opcional — para estratégias que não usam (todas exceto affinity)
        # economizamos não calculando.
        for _ in range(cfg.tickets_per_contest):
            ticket = generate_with_strategy(
                cfg.strategy,
                spec,
                stats,
                n_picked,
                rng=rng,
            )
            hits = len(set(ticket) & target_set)
            distribution.add(hits)
            total_hits += hits
        contests_tested += 1

    expected_hits = (
        total_hits / distribution.total_tickets if distribution.total_tickets else 0.0
    )
    return BacktestResult(
        config=cfg,
        distribution=distribution,
        contests_tested=contests_tested,
        expected_hits_per_ticket=expected_hits,
    )


def theoretical_expected_hits(spec: GameSpec, n_picked: int) -> float:
    """
    Esperança teórica de acertos com aposta uniforme:
        E[hits] = n_picked * draw_size / universe

    Se o backtest devolve algo estatisticamente diferente disso, ou a
    estratégia ESTÁ enviesando os resultados (pode ser bom ou ruim) ou
    há um bug. Tipicamente é a segunda hipótese.
    """
    return n_picked * spec.draw_size / spec.universe
