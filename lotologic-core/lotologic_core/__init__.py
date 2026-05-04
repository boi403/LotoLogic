"""
lotologic-core — motor de análise e geração de jogos para loterias da CAIXA.
"""

from .analysis.frequency import (
    FrequencyStats,
    compute_frequency_stats,
    top_delayed,
    top_frequent,
    window_stats,
)
from .analysis.pairs import (
    affinity_score,
    cooccurrence_matrix,
    normalized_affinity,
    top_pairs,
)
from .analysis.quality_score import (
    QualityBreakdown,
    evaluate_ticket,
)
from .backtest.runner import (
    BacktestConfig,
    BacktestResult,
    run_backtest,
    theoretical_expected_hits,
)
from .data.caixa_api import CaixaApiClient, CaixaApiError
from .domain.lottery import (
    LOTERIAS,
    Draw,
    GameSpec,
    Ticket,
    get_spec,
)
from .generators.covering import greedy_covering
from .generators.genetic import GAConfig, GAResult, TicketGA
from .generators.pareto import ParetoConfig, ParetoResult, optimize_portfolio
from .generators.strategies import (
    STRATEGIES,
    STRATEGY_ALIASES,
    generate_with_strategy,
)

__version__ = "0.1.0"

__all__ = [
    "LOTERIAS", "Draw", "GameSpec", "Ticket", "get_spec",
    "FrequencyStats", "QualityBreakdown", "affinity_score",
    "compute_frequency_stats", "cooccurrence_matrix", "evaluate_ticket",
    "normalized_affinity", "top_delayed", "top_frequent", "top_pairs",
    "window_stats",
    "GAConfig", "GAResult", "ParetoConfig", "ParetoResult",
    "STRATEGIES", "STRATEGY_ALIASES", "TicketGA",
    "generate_with_strategy", "greedy_covering", "optimize_portfolio",
    "BacktestConfig", "BacktestResult", "run_backtest",
    "theoretical_expected_hits",
    "CaixaApiClient", "CaixaApiError",
]
