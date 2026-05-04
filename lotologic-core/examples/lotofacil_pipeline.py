"""
Exemplo: pipeline completo da Lotofácil (modo demo, offline).

Demonstra como combinar todos os módulos do pacote.

Uso:
    python examples/lotofacil_pipeline.py
"""

import numpy as np

from lotologic_core import (
    GAConfig,
    TicketGA,
    compute_frequency_stats,
    cooccurrence_matrix,
    evaluate_ticket,
    get_spec,
    optimize_portfolio,
    ParetoConfig,
)
from lotologic_core.cli import _generate_demo_history


def main() -> None:
    spec = get_spec("lotofacil")
    print(f"=== {spec.name} ===\n")

    # --- 1. Histórico (sintético para reprodutibilidade) ---------------------
    history = _generate_demo_history("lotofacil", n=300, seed=42)
    print(f"Histórico: {len(history)} concursos sintéticos")

    # --- 2. Estatísticas -----------------------------------------------------
    stats = compute_frequency_stats(history, spec)
    cooc = cooccurrence_matrix(history, spec)
    print(f"Top 5 mais frequentes:")
    top5 = sorted(
        zip(range(1, 26), stats.absolute), key=lambda p: -p[1]
    )[:5]
    for n, c in top5:
        print(f"  {n:02d}  {c}x")

    # --- 3. Algoritmo Genético -----------------------------------------------
    print("\nRodando AG (pop=100, gen=150)...")
    ga = TicketGA(
        spec,
        stats,
        n_numbers=15,
        cooc=cooc,
        config=GAConfig(population_size=100, n_generations=150, seed=42),
    )
    result = ga.run()
    print(f"  Melhor score: {result.best_score:.2f}/100")
    print(f"  Bilhete:      {' - '.join(f'{n:02d}' for n in result.best_ticket)}")
    print(f"  Convergiu em {result.generations_run} gerações (early_stop={result.converged_early})")

    print("\n  Raio-X (componentes 0..100):")
    for k, v in result.breakdown.as_dict().items():
        if k != "total":
            print(f"    {k:<15} {v:6.1f}")

    # --- 4. Otimização de portfólio (SuperLab) -------------------------------
    print("\n--- Portfólio Pareto (5 bilhetes diversificados) ---")
    portfolio = optimize_portfolio(
        spec,
        stats,
        portfolio_size=5,
        n_numbers_per_ticket=15,
        cooc=cooc,
        config=ParetoConfig(seed=42),
    )
    for i, t in enumerate(portfolio.portfolio, 1):
        score = evaluate_ticket(t, spec, stats, cooc).total
        print(f"  [{i}] {' - '.join(f'{n:02d}' for n in t)}  score={score:.1f}")

    print(f"\n  Diversidade: {portfolio.components['diversity']:.3f}")
    print(f"  Cobertura de pares: {portfolio.components['pair_coverage']:.3f}")


if __name__ == "__main__":
    main()
