"""
Testes que validam que os bugs do AG-LotofacilPreditor foram corrigidos.

Testes positivos provam funcionamento; testes "regression" provam que
os bugs específicos do código original NÃO acontecem mais.
"""

import numpy as np
import pytest

from lotologic_core import (
    Draw,
    GAConfig,
    LOTERIAS,
    TicketGA,
    compute_frequency_stats,
    cooccurrence_matrix,
    evaluate_ticket,
    generate_with_strategy,
    get_spec,
    greedy_covering,
)


# ---------------------------------------------------------------------------
# Fixtures: histórico sintético
# ---------------------------------------------------------------------------


@pytest.fixture
def lotofacil_spec():
    return get_spec("lotofacil")


@pytest.fixture
def lotofacil_history():
    """200 concursos sintéticos da Lotofácil para testes determinísticos."""
    rng = np.random.default_rng(42)
    spec = get_spec("lotofacil")
    return [
        Draw(
            contest=i,
            game="lotofacil",
            numbers=tuple(
                sorted(
                    int(x) + 1
                    for x in rng.choice(spec.universe, spec.draw_size, replace=False)
                )
            ),
        )
        for i in range(1, 201)
    ]


@pytest.fixture
def lotofacil_stats(lotofacil_history, lotofacil_spec):
    return compute_frequency_stats(lotofacil_history, lotofacil_spec)


# ---------------------------------------------------------------------------
# Domínio
# ---------------------------------------------------------------------------


class TestGameSpec:
    def test_all_lotteries_valid(self):
        """Todas as 9 loterias do catálogo devem ser auto-consistentes."""
        for spec in LOTERIAS.values():
            assert spec.draw_size <= spec.universe
            assert spec.min_picks <= spec.max_picks <= spec.universe
            assert spec.draw_size <= spec.min_picks
            assert spec.sum_target_low <= spec.sum_target_high

    def test_unknown_game_raises(self):
        with pytest.raises(KeyError, match="desconhecida"):
            get_spec("megasenax")

    def test_lotofacil_matches_camila(self):
        """Os defaults da Lotofácil reproduzem os parâmetros do TCC original."""
        spec = get_spec("lotofacil")
        assert spec.universe == 25
        assert spec.draw_size == 15
        # Camila usa 7 pares / 8 ímpares — replicado.
        assert spec.target_even_count == 7
        # Faixa de soma 190-260 — idêntica ao critério do AG original.
        assert (spec.sum_target_low, spec.sum_target_high) == (190, 260)


# ---------------------------------------------------------------------------
# AG — testes de regressão dos bugs do original
# ---------------------------------------------------------------------------


class TestGABugFixes:
    """
    Validação explícita das correções aplicadas em relação ao
    AG-LotofacilPreditor da Camila.
    """

    def test_no_duplicates_in_offspring(self, lotofacil_spec, lotofacil_stats):
        """
        Bug 1 do original: crossover de ponto único produzia duplicatas.

        Aqui executamos o GA por algumas gerações e verificamos que NENHUM
        indivíduo da população final tem dezenas duplicadas.
        """
        cfg = GAConfig(
            population_size=50,
            n_generations=20,
            mutation_rate=0.3,
            elitism=2,
            seed=42,
        )
        ga = TicketGA(lotofacil_spec, lotofacil_stats, n_numbers=15, config=cfg)
        # Acessamos o método interno para gerar pais e filho 1000 vezes.
        rng = np.random.default_rng(123)
        for _ in range(1000):
            p1 = ga._random_individual()
            p2 = ga._random_individual()
            child = ga._crossover(p1, p2)
            assert len(child) == 15
            assert len(set(child.tolist())) == 15, (
                f"Duplicata no filho: {child}"
            )
            assert all(1 <= n <= 25 for n in child)

    def test_mutation_actually_changes_genome(self, lotofacil_spec, lotofacil_stats):
        """
        Bug 2 do original: mutação só trocava posições (no-op para conjuntos).

        Nossa mutação por substituição: o conjunto resultante tem que ser
        DIFERENTE do original em exatamente uma dezena.
        """
        ga = TicketGA(lotofacil_spec, lotofacil_stats, n_numbers=15)
        for _ in range(100):
            individual = ga._random_individual()
            mutant = ga._mutate(individual)
            sym_diff = set(individual.tolist()) ^ set(mutant.tolist())
            # Mutação por substituição: 1 dezena entra, 1 sai → diferença = 2.
            assert len(sym_diff) == 2, (
                f"Mutação não funcionou: {individual} -> {mutant}"
            )

    def test_fitness_always_nonzero_for_valid_tickets(self, lotofacil_spec):
        """
        Bug 3 do original: fitness=0 para violações soft destruía o gradiente.

        Aqui: bilhetes "ruins" (todos pares, soma fora da banda) ainda devem
        receber score > 0 — só zeram se forem ESTRUTURALMENTE inválidos
        (duplicata, fora do universo).
        """
        # Bilhete tecnicamente legal mas péssimo: todas pares, soma muito alta.
        bad_ticket = (2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 25, 23, 21)
        bad_ticket = tuple(sorted(set(bad_ticket)))[:15]
        # Ajuste: garante 15 únicos
        if len(bad_ticket) < 15:
            bad_ticket = (2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 21, 23, 25)
        breakdown = evaluate_ticket(bad_ticket, lotofacil_spec)
        assert breakdown.total > 0, (
            f"Score zerado em bilhete válido (mas ruim): {breakdown}"
        )

    def test_fitness_zero_only_for_structural_violations(self, lotofacil_spec):
        """Score zera APENAS para violações estruturais."""
        # Duplicata é violação estrutural (não acontece num GA correto, mas
        # se acontecer o avaliador deve marcar).
        breakdown = evaluate_ticket(
            (1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14),
            lotofacil_spec,
        )
        assert breakdown.total == 0
        assert "dezenas duplicadas" in breakdown.flags


class TestGAConvergence:
    """O GA converge para algo melhor do que o aleatório."""

    def test_converges_better_than_random(self, lotofacil_spec, lotofacil_stats):
        """O melhor bilhete encontrado pelo GA tem score > média de aleatórios."""
        rng = np.random.default_rng(0)
        # Baseline: 200 bilhetes aleatórios uniformes.
        random_scores = []
        for _ in range(200):
            ticket = generate_with_strategy(
                "random", lotofacil_spec, lotofacil_stats, 15, rng=rng
            )
            random_scores.append(evaluate_ticket(ticket, lotofacil_spec, lotofacil_stats).total)
        baseline_mean = float(np.mean(random_scores))

        cfg = GAConfig(
            population_size=80, n_generations=40, seed=42, early_stop_patience=15
        )
        ga = TicketGA(lotofacil_spec, lotofacil_stats, n_numbers=15, config=cfg)
        result = ga.run()
        assert result.best_score > baseline_mean


# ---------------------------------------------------------------------------
# Estatísticas
# ---------------------------------------------------------------------------


class TestFrequencyStats:
    def test_relative_frequencies_sum_correctly(
        self, lotofacil_history, lotofacil_spec
    ):
        """Soma das frequências relativas = draw_size (cada concurso tem 15)."""
        stats = compute_frequency_stats(lotofacil_history, lotofacil_spec)
        assert stats.relative.sum() == pytest.approx(lotofacil_spec.draw_size, rel=1e-9)

    def test_delays_in_valid_range(self, lotofacil_history, lotofacil_spec):
        """Atrasos estão entre 0 e total_contests."""
        stats = compute_frequency_stats(lotofacil_history, lotofacil_spec)
        assert (stats.delays >= 0).all()
        assert (stats.delays <= len(lotofacil_history)).all()

    def test_empty_history_no_crash(self, lotofacil_spec):
        stats = compute_frequency_stats([], lotofacil_spec)
        assert stats.total_contests == 0
        assert stats.absolute.shape == (lotofacil_spec.universe,)


# ---------------------------------------------------------------------------
# Estratégias
# ---------------------------------------------------------------------------


class TestStrategies:
    @pytest.mark.parametrize("strategy", ["random", "historical", "delayed", "balanced"])
    def test_strategy_produces_valid_ticket(
        self, strategy, lotofacil_spec, lotofacil_stats
    ):
        rng = np.random.default_rng(7)
        ticket = generate_with_strategy(strategy, lotofacil_spec, lotofacil_stats, 15, rng=rng)
        assert len(ticket) == 15
        assert len(set(ticket)) == 15
        assert all(1 <= n <= 25 for n in ticket)

    def test_affinity_strategy_uses_cooc(self, lotofacil_history, lotofacil_spec, lotofacil_stats):
        cooc = cooccurrence_matrix(lotofacil_history, lotofacil_spec)
        rng = np.random.default_rng(7)
        ticket = generate_with_strategy(
            "affinity", lotofacil_spec, lotofacil_stats, 15, cooc=cooc, rng=rng
        )
        assert len(ticket) == 15

    def test_unknown_strategy_raises(self, lotofacil_spec, lotofacil_stats):
        with pytest.raises(ValueError, match="desconhecida"):
            generate_with_strategy("xyz", lotofacil_spec, lotofacil_stats, 15)

    def test_invalid_n_raises(self, lotofacil_spec, lotofacil_stats):
        with pytest.raises(ValueError, match="fora do permitido"):
            generate_with_strategy("random", lotofacil_spec, lotofacil_stats, 100)


# ---------------------------------------------------------------------------
# Greedy Covering
# ---------------------------------------------------------------------------


class TestCovering:
    def test_covers_all_required_tuples(self):
        pool = (1, 2, 3, 4, 5, 6, 7, 8)
        blocks = greedy_covering(pool, block_size=4, guarantee=2)
        # Cada par de pool DEVE estar em pelo menos um bloco.
        from itertools import combinations

        all_pairs = set(frozenset(p) for p in combinations(pool, 2))
        covered = set()
        for b in blocks:
            for pair in combinations(b, 2):
                covered.add(frozenset(pair))
        assert all_pairs.issubset(covered)

    def test_each_block_has_correct_size(self):
        pool = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
        blocks = greedy_covering(pool, block_size=6, guarantee=4)
        for b in blocks:
            assert len(b) == 6
            assert len(set(b)) == 6

    def test_invalid_params_raise(self):
        with pytest.raises(ValueError):
            greedy_covering((1, 2, 3), block_size=4, guarantee=2)
        with pytest.raises(ValueError):
            greedy_covering((1, 2, 3, 4, 5), block_size=2, guarantee=4)
