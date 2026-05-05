"""
CLI do lotologic-core.

Uso:
    python -m lotologic_core.cli list
    python -m lotologic_core.cli stats megasena --history demo
    python -m lotologic_core.cli generate megasena --strategy balanced --n 6
    python -m lotologic_core.cli ga lotofacil --history demo
    python -m lotologic_core.cli backtest megasena --strategy delayed --history demo
    python -m lotologic_core.cli covering --pool 1,3,5,7,9,11,13,15 --k 6 --t 4

Para testar sem rede, use `--history demo` (gera concursos sintéticos).
Para usar dados reais, omita `--history` (busca da API da Caixa).
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

import numpy as np

from .analysis.frequency import compute_frequency_stats, top_delayed, top_frequent
from .analysis.pairs import cooccurrence_matrix
from .analysis.quality_score import evaluate_ticket
from .backtest.runner import (
    BacktestConfig,
    run_backtest,
    theoretical_expected_hits,
)
from .data.caixa_api import CaixaApiClient, CaixaApiError
from .domain.lottery import LOTERIAS, Draw, get_spec
from .generators.covering import greedy_covering
from .generators.genetic import GAConfig, TicketGA
from .generators.pareto import ParetoConfig, optimize_portfolio
from .generators.strategies import STRATEGIES, generate_with_strategy


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _generate_demo_history(game: str, n: int = 200, seed: int = 42) -> list[Draw]:
    """Gera concursos sintéticos para testes offline."""
    spec = get_spec(game)
    rng = np.random.default_rng(seed)
    draws = []
    for i in range(1, n + 1):
        nums = tuple(
            sorted(int(x) for x in rng.choice(spec.universe, spec.draw_size, replace=False) + 1)
        )
        draws.append(Draw(contest=i, game=game, numbers=nums))
    return draws


def _load_history(game: str, source: Optional[str], limit: Optional[int]) -> list[Draw]:
    """
    Carrega histórico.

    `source`:
      - 'demo' → gera concursos sintéticos (offline, reprodutível com seed)
      - 'cache' → usa só o cache local; falha se cache vazio
      - 'live' / None → cache local + sincronização incremental com a API
    """
    if source == "demo":
        return _generate_demo_history(game, n=limit or 200)

    # Importação local pra não obrigar quem usa só 'demo' a ter requests etc.
    from .data.cache import load_cache, sync_game

    if source == "cache":
        cached = load_cache(game)
        if not cached:
            print(
                f"⚠️  Cache vazio para {game}. Rode `sync {game}` primeiro.",
                file=sys.stderr,
            )
            sys.exit(2)
        return cached[-(limit or 200):] if limit else cached

    # source = 'live' ou None: usa cache + sincroniza incrementalmente
    try:
        print(f"Sincronizando cache de {game}...", file=sys.stderr)

        def _progress(c, target):
            if c % 10 == 0 or c == target:
                print(f"  baixando concurso {c}/{target}...", file=sys.stderr)

        n_total, n_new = sync_game(game, progress_cb=_progress)
        if n_new > 0:
            print(f"  ✓ {n_new} concurso(s) novo(s) baixado(s)", file=sys.stderr)
        else:
            print(f"  ✓ cache já estava atualizado ({n_total} concursos)", file=sys.stderr)
    except CaixaApiError as e:
        print(f"⚠️  Falha ao acessar API: {e}", file=sys.stderr)
        # Tenta cair pra cache se houver
        from .data.cache import load_cache as _lc
        cached = _lc(game)
        if cached:
            print(f"    Usando cache offline ({len(cached)} concursos)", file=sys.stderr)
            return cached[-(limit or 200):] if limit else cached
        print("    Sem cache. Use --history demo para dados sintéticos", file=sys.stderr)
        sys.exit(2)

    cached = load_cache(game)
    return cached[-(limit or 200):] if limit else cached


def _format_ticket(numbers: tuple[int, ...]) -> str:
    return " - ".join(f"{n:02d}" for n in numbers)


# ---------------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------------


def cmd_list(args: argparse.Namespace) -> int:
    print("Loterias suportadas:")
    for key, spec in LOTERIAS.items():
        print(
            f"  {key:14s} {spec.name:14s} "
            f"universe={spec.universe:3d} draw={spec.draw_size:2d} "
            f"picks={spec.min_picks}..{spec.max_picks}"
        )
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    spec = get_spec(args.game)
    history = _load_history(args.game, args.history, args.limit)
    stats = compute_frequency_stats(history, spec)
    print(f"\n{spec.name} — {stats.total_contests} concursos")
    print(f"\n  Top 10 mais frequentes:")
    for n, count in top_frequent(stats, 10):
        print(f"    {n:02d}  {count:5d}x  ({100*count/stats.total_contests:5.1f}%)")
    print(f"\n  Top 10 mais atrasadas:")
    for n, delay in top_delayed(stats, 10):
        print(f"    {n:02d}  atraso de {delay:3d} concursos")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    spec = get_spec(args.game)
    history = _load_history(args.game, args.history, args.limit)
    stats = compute_frequency_stats(history, spec)
    n_numbers = args.n or spec.min_picks
    cooc = cooccurrence_matrix(history, spec) if args.strategy in ("affinity",) else None

    rng = np.random.default_rng(args.seed)
    print(f"\n{spec.name} — estratégia '{args.strategy}', {args.count} bilhete(s):")
    for i in range(args.count):
        ticket = generate_with_strategy(
            args.strategy, spec, stats, n_numbers, cooc=cooc, rng=rng
        )
        breakdown = evaluate_ticket(ticket, spec, stats, cooc)
        print(f"  [{i+1:02d}] {_format_ticket(ticket)}   score={breakdown.total:5.1f}")
    return 0


def cmd_ga(args: argparse.Namespace) -> int:
    spec = get_spec(args.game)
    history = _load_history(args.game, args.history, args.limit)
    stats = compute_frequency_stats(history, spec)
    cooc = cooccurrence_matrix(history, spec)
    n_numbers = args.n or spec.min_picks

    cfg = GAConfig(
        population_size=args.pop,
        n_generations=args.gen,
        seed=args.seed,
    )
    ga = TicketGA(spec, stats, n_numbers=n_numbers, cooc=cooc, config=cfg)
    print(f"\n{spec.name} — Algoritmo Genético (pop={cfg.population_size}, gen={cfg.n_generations})")
    print("Rodando...", file=sys.stderr)
    result = ga.run()

    print(f"\n  Melhor bilhete: {_format_ticket(result.best_ticket)}")
    print(f"  Score: {result.best_score:.2f}/100")
    print(f"  Gerações: {result.generations_run} (early_stop={result.converged_early})")
    print(f"\n  X-Ray:")
    b = result.breakdown
    print(f"    paridade        {b.parity:5.1f}")
    print(f"    soma            {b.sum_band:5.1f}")
    print(f"    cobertura       {b.range_coverage:5.1f}")
    print(f"    sequências      {b.sequences:5.1f}")
    print(f"    frequência      {b.frequency:5.1f}")
    print(f"    atraso          {b.delay:5.1f}")
    print(f"    afinidade       {b.affinity:5.1f}")
    return 0


def cmd_backtest(args: argparse.Namespace) -> int:
    spec = get_spec(args.game)
    history = _load_history(args.game, args.history, args.limit)
    n_numbers = args.n or spec.min_picks

    cfg = BacktestConfig(
        strategy=args.strategy,
        n_numbers=n_numbers,
        tickets_per_contest=args.tickets,
        seed=args.seed,
    )
    print(f"\nBacktest {spec.name}, estratégia '{args.strategy}'...", file=sys.stderr)
    result = run_backtest(spec, history, cfg)
    theoretical = theoretical_expected_hits(spec, n_numbers)

    print(f"\n  Concursos testados: {result.contests_tested}")
    print(f"  Bilhetes simulados: {result.distribution.total_tickets}")
    print(f"  Acertos médios:     {result.expected_hits_per_ticket:.3f}")
    print(f"  Esperança uniforme: {theoretical:.3f}")
    print(f"  Diferença:          {result.expected_hits_per_ticket - theoretical:+.3f}")
    print(f"\n  Distribuição de acertos:")
    for h in sorted(result.distribution.counts.keys()):
        prob = result.distribution.probability(h)
        bar = "█" * min(int(prob * 200), 60)
        print(f"    {h:2d} acertos: {prob*100:5.2f}% {bar}")
    return 0


def cmd_pareto(args: argparse.Namespace) -> int:
    spec = get_spec(args.game)
    history = _load_history(args.game, args.history, args.limit)
    stats = compute_frequency_stats(history, spec)
    cooc = cooccurrence_matrix(history, spec)
    n_numbers = args.n or spec.min_picks

    cfg = ParetoConfig(
        weight_frequency=args.wf,
        weight_diversity=args.wd,
        weight_pair_coverage=args.wp,
        n_candidates=args.candidates,
        seed=args.seed,
    )
    print(f"\n{spec.name} — Otimizador Pareto (portfolio={args.size})")
    result = optimize_portfolio(spec, stats, args.size, n_numbers, cfg, cooc)

    print(f"\n  Score combinado: {result.score:.4f}")
    print(f"  Componentes: {json.dumps(result.components, indent=4)}")
    print(f"\n  Portfólio ({len(result.portfolio)} bilhetes):")
    for i, ticket in enumerate(result.portfolio, 1):
        print(f"    [{i:02d}] {_format_ticket(ticket)}")
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    """Sincroniza o cache local com a API da Caixa."""
    from .data.cache import sync_game, get_cache_dir

    targets = list(LOTERIAS.keys()) if args.game == "all" else [args.game]
    print(f"Diretório de cache: {get_cache_dir()}\n")

    total_new = 0
    for game in targets:
        spec = get_spec(game)
        print(f"=== {spec.name} ({game}) ===")

        def _progress(c, target):
            if c == target or c % 25 == 0:
                pct = 100 * c / target if target else 0
                print(f"  {c}/{target} ({pct:.0f}%)", end="\r", file=sys.stderr)

        try:
            n_total, n_new = sync_game(
                game, full_resync=args.full, progress_cb=_progress
            )
            print(f"  ✓ {n_total} concursos no cache (+{n_new} novos)        ")
            total_new += n_new
        except CaixaApiError as e:
            print(f"  ✗ erro: {e}")

    print(f"\nSync concluído. {total_new} concurso(s) novo(s) no total.")
    return 0


def cmd_cache_info(args: argparse.Namespace) -> int:
    """Mostra estado do cache local."""
    from .data.cache import cache_summary, get_cache_dir

    cache_dir = get_cache_dir()
    print(f"Cache em: {cache_dir}\n")

    summary = cache_summary()
    if not summary:
        print("Cache vazio. Rode `sync all` para baixar concursos.")
        return 0

    print(f"{'Loteria':14s} {'Concursos':>10s}  {'Faixa':>15s}  {'Última sync':>20s}")
    print("-" * 65)
    for game, info in sorted(summary.items()):
        faixa = f"{info['first_contest']}-{info['last_contest']}"
        synced = (info.get("last_synced") or "")[:19]
        print(f"{game:14s} {info['n_draws']:>10d}  {faixa:>15s}  {synced:>20s}")
    return 0



def cmd_covering(args: argparse.Namespace) -> int:
    pool = tuple(int(x) for x in args.pool.split(","))
    print(
        f"\nDesdobramento Greedy: pool={pool} ({len(pool)} dezenas), "
        f"bilhete={args.k}, garantia={args.t}"
    )
    blocks = greedy_covering(
        pool, args.k, args.t, rng=np.random.default_rng(args.seed)
    )
    print(f"\n  {len(blocks)} bilhetes gerados:")
    for i, b in enumerate(blocks, 1):
        print(f"    [{i:03d}] {_format_ticket(b)}")
    return 0


# ---------------------------------------------------------------------------
# Wiring
# ---------------------------------------------------------------------------


def _add_history_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--history",
        choices=["demo", "live", "cache"],
        default="live",
        help=(
            "'demo' usa concursos sintéticos (offline); "
            "'cache' usa só o cache local sem rede; "
            "'live' usa cache + sincronização incremental com a Caixa (default)"
        ),
    )
    p.add_argument(
        "--limit", type=int, default=200, help="Quantos concursos usar (default 200)"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lotologic-core",
        description="Motor de análise e geração de jogos para loterias da CAIXA.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="Lista loterias suportadas")

    p_stats = sub.add_parser("stats", help="Estatísticas de uma loteria")
    p_stats.add_argument("game")
    _add_history_flags(p_stats)

    p_gen = sub.add_parser("generate", help="Gera bilhetes via estratégia")
    p_gen.add_argument("game")
    p_gen.add_argument("--strategy", choices=list(STRATEGIES.keys()), default="balanced")
    p_gen.add_argument("--count", type=int, default=5)
    p_gen.add_argument("--n", type=int, default=None, help="Dezenas por bilhete")
    p_gen.add_argument("--seed", type=int, default=None)
    _add_history_flags(p_gen)

    p_ga = sub.add_parser("ga", help="Algoritmo Genético (versão corrigida)")
    p_ga.add_argument("game")
    p_ga.add_argument("--pop", type=int, default=200)
    p_ga.add_argument("--gen", type=int, default=100)
    p_ga.add_argument("--n", type=int, default=None)
    p_ga.add_argument("--seed", type=int, default=None)
    _add_history_flags(p_ga)

    p_bt = sub.add_parser("backtest", help="Backtest contra histórico")
    p_bt.add_argument("game")
    p_bt.add_argument("--strategy", choices=list(STRATEGIES.keys()), default="balanced")
    p_bt.add_argument("--tickets", type=int, default=10)
    p_bt.add_argument("--n", type=int, default=None)
    p_bt.add_argument("--seed", type=int, default=None)
    _add_history_flags(p_bt)

    p_pa = sub.add_parser("pareto", help="Otimização Pareto multi-objetivo")
    p_pa.add_argument("game")
    p_pa.add_argument("--size", type=int, default=10)
    p_pa.add_argument("--n", type=int, default=None)
    p_pa.add_argument("--wf", type=float, default=1.0, help="Peso frequência")
    p_pa.add_argument("--wd", type=float, default=1.0, help="Peso diversidade")
    p_pa.add_argument("--wp", type=float, default=1.0, help="Peso cobertura de pares")
    p_pa.add_argument("--candidates", type=int, default=200)
    p_pa.add_argument("--seed", type=int, default=None)
    _add_history_flags(p_pa)

    p_cov = sub.add_parser("covering", help="Desdobramento (Greedy Covering Design)")
    p_cov.add_argument("--pool", required=True, help="Dezenas separadas por vírgula")
    p_cov.add_argument("--k", type=int, required=True, help="Tamanho do bilhete")
    p_cov.add_argument("--t", type=int, required=True, help="Garantia (faixa)")
    p_cov.add_argument("--seed", type=int, default=None)

    p_sync = sub.add_parser(
        "sync", help="Baixa/atualiza cache local de concursos da Caixa"
    )
    p_sync.add_argument(
        "game",
        help="Nome da loteria (megasena, lotofacil, ...) ou 'all' para todas",
    )
    p_sync.add_argument(
        "--full",
        action="store_true",
        help="Re-baixa tudo do zero (ignora cache existente)",
    )

    sub.add_parser(
        "cache-info", help="Mostra estado do cache local de concursos"
    )

    return parser


COMMAND_DISPATCH = {
    "list": cmd_list,
    "stats": cmd_stats,
    "generate": cmd_generate,
    "ga": cmd_ga,
    "backtest": cmd_backtest,
    "pareto": cmd_pareto,
    "covering": cmd_covering,
    "sync": cmd_sync,
    "cache-info": cmd_cache_info,
}


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    handler = COMMAND_DISPATCH[args.cmd]
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
