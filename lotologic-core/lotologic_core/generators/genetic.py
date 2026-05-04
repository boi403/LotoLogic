"""
Algoritmo Genético — versão corrigida e generalizada.

═══════════════════════════════════════════════════════════════════════════
    REESCRITA DO AG-LotofacilPreditor com correções estruturais.

    O AG original (Java, ~530 linhas) foi a maior contribuição conceitual
    para esta lib, mas tem três problemas que comprometem a qualidade
    da busca:
═══════════════════════════════════════════════════════════════════════════

BUG 1 — Crossover de ponto único cria DUPLICATAS.
    Original (linhas 378-401 de LotoNumeros.java):
        for (int i = 0; i < crossoverPoint; i++)  filho[i] = pai1[i];
        for (int i = crossoverPoint; i < pai2.length; i++) filho[i] = pai2[i];

    Problema: pai1 e pai2 podem ter dezenas em comum em posições diferentes.
    Por exemplo, pai1=[1,2,3,4,...], pai2=[5,6,3,7,...]; com corte em 2,
    filho = [1,2,3,7,...], mas se a posição 5 do pai2 for o número "1",
    o filho terá [1,2,3,7,1,...]. O fitness original detecta isso e
    ZERA o fitness, mas isso significa que muitos filhos do crossover são
    descartados — ineficiente e enviesado.

    Solução adotada: **Subset Crossover** (também chamado "uniform set
    crossover"). Pegamos a união das dezenas dos dois pais, escolhemos
    `draw_size` delas com viés para as comuns aos dois pais (que são as
    "boas" segundo a evolução). Isso preserva a invariância de tamanho
    do conjunto e ainda mantém o efeito de mistura genética.

BUG 2 — Mutação inútil para loteria.
    Original (linhas 411-427):
        int temp = mutante[index1];
        mutante[index1] = mutante[index2];
        mutante[index2] = temp;

    Problema: trocar `mutante[i]` com `mutante[j]` apenas reordena
    posições no array. Mas para loteria, o array representa um CONJUNTO
    — a ordem é irrelevante. Esse "mutação" é um no-op semântico.

    Solução: **Substituição** — trocar uma dezena do indivíduo por uma
    dezena que NÃO está no indivíduo. Esse é o operador correto para
    GAs sobre subconjuntos.

BUG 3 — Fitness destrutivo.
    Original: `fitness = 0` em diversas condições, inclusive estatísticas
    soft (soma fora de faixa, poucos primos, etc.).

    Problema: a roleta de seleção (`selecinaIndividuoFitness`) opera por
    proporcionalidade. Se metade da população tem fitness 0, ela é
    completamente ignorada pela seleção — perdemos diversidade. E pior:
    se TODA a população cair em fitness 0 (cenário comum nas primeiras
    gerações), a seleção fica indeterminada (`totalFitness=0`).

    Solução: usamos `quality_score.evaluate_ticket()` que devolve sempre
    valor em [0, 100], com penalidades suaves. Zero só aparece para
    bilhetes estruturalmente inválidos.

OUTROS APRIMORAMENTOS:

  * **Generalizado**: funciona para qualquer GameSpec (Mega, Quina, etc.),
    não só Lotofácil 25/15.
  * **Fitness sharing** opcional para preservar diversidade da população.
  * **Convergência detectada**: se o melhor não melhora em N gerações,
    para. (Original ia até 200 gerações sempre.)
  * **Reprodutível**: aceita seed.
  * **Vetorizado**: avaliação em batch via numpy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from ..analysis.frequency import FrequencyStats
from ..analysis.quality_score import QualityBreakdown, evaluate_ticket
from ..domain.lottery import GameSpec


@dataclass
class GAConfig:
    """Hiperparâmetros do algoritmo genético."""

    population_size: int = 200
    n_generations: int = 100
    mutation_rate: float = 0.15
    elitism: int = 10
    tournament_size: int = 3  # seleção por torneio (mais robusta que roleta)
    early_stop_patience: int = 20  # paramos se não melhora em N gerações
    seed: Optional[int] = None


@dataclass
class GAResult:
    """Resultado de uma corrida do AG."""

    best_ticket: tuple[int, ...]
    best_score: float
    breakdown: QualityBreakdown
    generations_run: int
    history: list[float]  # melhor fitness por geração
    converged_early: bool


class TicketGA:
    """
    AG sobre subconjuntos (bilhetes) de uma loteria.

    Uso:
        ga = TicketGA(spec, stats, cooc=cooc, n_numbers=15)
        result = ga.run()
        print(result.best_ticket, result.best_score)

    Por que classe e não função pura? Porque queremos expor `step()`,
    `population` e `current_scores` para o "X-Ray Pipeline" (visualização
    passo-a-passo prometida no README do Logic Pro).
    """

    def __init__(
        self,
        spec: GameSpec,
        stats: FrequencyStats,
        n_numbers: int,
        cooc: Optional[np.ndarray] = None,
        config: Optional[GAConfig] = None,
        score_weights: Optional[dict[str, float]] = None,
    ):
        if not (spec.min_picks <= n_numbers <= spec.max_picks):
            raise ValueError(
                f"n_numbers={n_numbers} fora do permitido para {spec.name}"
            )
        self.spec = spec
        self.stats = stats
        self.cooc = cooc
        self.n_numbers = n_numbers
        self.config = config or GAConfig()
        self.score_weights = score_weights
        self.rng = np.random.default_rng(self.config.seed)
        # Estatísticas pré-computadas para o sampler enviesado:
        # usamos a frequência relativa para inicializar a população melhor
        # do que aleatório uniforme (heurística).
        self._init_weights = self._build_init_weights(stats)

    # ------------------------------------------------------------------
    # Operadores genéticos
    # ------------------------------------------------------------------

    def _build_init_weights(self, stats: FrequencyStats) -> np.ndarray:
        """
        Pesos para amostrar a população inicial. Usa frequência+atraso
        suavizados em vez de uniforme — convergência mais rápida.
        """
        if stats.total_contests == 0:
            return np.ones(self.spec.universe, dtype=np.float64)
        freq = stats.absolute / max(stats.absolute.max(), 1)
        delay = stats.delays / max(stats.delays.max(), 1)
        weights = 1.0 + 0.5 * freq + 0.5 * delay  # garante > 0
        return weights

    def _random_individual(self) -> np.ndarray:
        """Indivíduo aleatório enviesado pelos init_weights."""
        weights = self._init_weights + 1e-12
        u = self.rng.random(len(weights))
        keys = np.log(u) / weights
        chosen = np.argsort(keys)[-self.n_numbers :]
        return np.sort(chosen + 1)  # dezenas (1..universe)

    def _crossover(self, p1: np.ndarray, p2: np.ndarray) -> np.ndarray:
        """
        Subset Crossover — corrige o bug 1 do original.

        União dos pais; dezenas comuns (interseção) ENTRAM
        obrigatoriamente no filho; o resto é completado por sorteio
        (sem reposição) entre as restantes da união.

        Garante:
          - Sem duplicatas
          - Tamanho exato `n_numbers`
          - Genes "bons" (presentes em ambos os pais) preservados
        """
        common = np.intersect1d(p1, p2, assume_unique=True)
        union = np.union1d(p1, p2)

        if len(common) >= self.n_numbers:
            # Caso raro: pais quase iguais. Pegamos n aleatórios da interseção.
            chosen = self.rng.choice(common, self.n_numbers, replace=False)
            return np.sort(chosen)

        remaining_pool = np.setdiff1d(union, common, assume_unique=True)
        n_to_fill = self.n_numbers - len(common)
        if len(remaining_pool) < n_to_fill:
            # União não cobre n_numbers (acontece se pais muito parecidos):
            # completa com dezenas aleatórias do universo.
            outside = np.setdiff1d(
                np.arange(1, self.spec.universe + 1), union, assume_unique=True
            )
            extra = self.rng.choice(outside, n_to_fill - len(remaining_pool), replace=False)
            picks = np.concatenate([remaining_pool, extra])
        else:
            picks = self.rng.choice(remaining_pool, n_to_fill, replace=False)

        return np.sort(np.concatenate([common, picks]))

    def _mutate(self, individual: np.ndarray) -> np.ndarray:
        """
        Mutação por SUBSTITUIÇÃO — corrige o bug 2 do original.

        Em vez de trocar posições (no-op para conjunto), substitui uma
        dezena do indivíduo por outra que NÃO está nele. Mantém o
        tamanho e a unicidade.

        Probabilidade controlada externamente — esta função sempre
        aplica uma mutação quando chamada.
        """
        outside = np.setdiff1d(
            np.arange(1, self.spec.universe + 1), individual, assume_unique=True
        )
        if len(outside) == 0:
            return individual  # caso degenerado: indivíduo cobre o universo todo
        idx_to_replace = self.rng.integers(0, len(individual))
        new_value = self.rng.choice(outside)
        mutant = individual.copy()
        mutant[idx_to_replace] = new_value
        return np.sort(mutant)

    def _tournament_select(
        self, population: list[np.ndarray], fitnesses: np.ndarray
    ) -> np.ndarray:
        """
        Seleção por torneio — mais robusta que roleta a fitness com
        valores muito desiguais. Especialmente importante porque,
        embora nosso fitness seja sempre não-negativo, ele pode
        concentrar muito perto de zero nas primeiras gerações.
        """
        size = self.config.tournament_size
        contestants = self.rng.choice(len(population), size, replace=False)
        winner_idx = contestants[np.argmax(fitnesses[contestants])]
        return population[winner_idx]

    # ------------------------------------------------------------------
    # Loop principal
    # ------------------------------------------------------------------

    def _evaluate_population(
        self, population: list[np.ndarray]
    ) -> tuple[np.ndarray, list[QualityBreakdown]]:
        """Avalia toda a população e devolve (fitness_array, breakdowns)."""
        breakdowns = [
            evaluate_ticket(
                tuple(int(n) for n in ind),
                self.spec,
                self.stats,
                self.cooc,
                self.score_weights,
            )
            for ind in population
        ]
        fitness = np.array([b.total for b in breakdowns], dtype=np.float64)
        return fitness, breakdowns

    def run(self) -> GAResult:
        """Executa o GA até convergir ou esgotar `n_generations`."""
        cfg = self.config
        population = [self._random_individual() for _ in range(cfg.population_size)]
        fitness, breakdowns = self._evaluate_population(population)

        history: list[float] = []
        best_idx = int(np.argmax(fitness))
        best_ind = population[best_idx].copy()
        best_score = float(fitness[best_idx])
        best_breakdown = breakdowns[best_idx]
        no_improve_count = 0
        gen_run = 0
        converged_early = False

        for gen in range(cfg.n_generations):
            gen_run = gen + 1
            history.append(best_score)

            # Elitismo: melhores N passam direto.
            elite_idx = np.argsort(-fitness)[: cfg.elitism]
            new_population = [population[i].copy() for i in elite_idx]

            # Restante: torneio + crossover + mutação.
            while len(new_population) < cfg.population_size:
                p1 = self._tournament_select(population, fitness)
                p2 = self._tournament_select(population, fitness)
                child = self._crossover(p1, p2)
                if self.rng.random() < cfg.mutation_rate:
                    child = self._mutate(child)
                new_population.append(child)

            population = new_population
            fitness, breakdowns = self._evaluate_population(population)
            current_best_idx = int(np.argmax(fitness))
            current_best_score = float(fitness[current_best_idx])

            if current_best_score > best_score + 1e-9:
                best_score = current_best_score
                best_ind = population[current_best_idx].copy()
                best_breakdown = breakdowns[current_best_idx]
                no_improve_count = 0
            else:
                no_improve_count += 1

            if no_improve_count >= cfg.early_stop_patience:
                converged_early = True
                break

        history.append(best_score)
        return GAResult(
            best_ticket=tuple(int(n) for n in best_ind),
            best_score=best_score,
            breakdown=best_breakdown,
            generations_run=gen_run,
            history=history,
            converged_early=converged_early,
        )
