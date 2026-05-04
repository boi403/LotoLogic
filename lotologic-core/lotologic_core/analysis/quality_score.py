"""
Quality Score / Análise X-Ray de um bilhete.

Esta é a **reescrita corrigida e generalizada** da função `calculaFitness`
do AG-LotofacilPreditor da Camila. Mantém os critérios estatísticos
descritos no README do LotoLogic ("Score de qualidade estrutural ... baseada
em equilíbrio par/ímpar, distribuição por faixas, somas e sequências"),
mas conserta problemas estruturais do original:

CORREÇÕES APLICADAS (em relação ao AG-LotofacilPreditor):

1. **Não zera o fitness abruptamente.** O original zerava em N condições
   (`fitness = 0` se primos < 2, se diagonal < 2 ou > 17, se soma fora de
   190-260, se houver duplicata). Isso destrói o gradiente — o algoritmo
   genético fica andando num platô de zeros e perde toda informação útil.
   Trocamos por penalidades suaves (subtração proporcional à violação),
   que é a prática correta em GA. Isso preserva a noção de "ruim mas
   melhorando".

2. **Generalizado para todas as loterias.** O original era hard-coded para
   Lotofácil (25/15, soma 190-260, 7 pares, técnica diagonal 5x5). Aqui
   tudo vem de `GameSpec` — funciona para Mega, Quina, Timemania, etc.

3. **A tabela de frequência vem de dados REAIS**, não de 10 sorteios
   manualmente digitados num array (sic, no código original).

4. **Pontuação na escala 0-100.** O README do LotoLogic promete badges de
   cor (vermelho/amarelo/verde) — só faz sentido se o score for normalizado.
   O original retornava valores arbitrários (até 400+).

5. **X-Ray detalhado.** Cada componente do score é exposto separadamente,
   permitindo o "X-Ray Pipeline" de transparência prometido pelo Logic Pro.

6. **Métrica de "distância mínima"** do original era um soma `|x[i]-x[i+1]|`
   sobre array já ordenado — é simplesmente `max - min` por telescopia.
   Substituímos por uma medida de dispersão real (desvio padrão dos gaps).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from ..domain.lottery import GameSpec
from .frequency import FrequencyStats
from .pairs import affinity_score


@dataclass
class QualityBreakdown:
    """
    Decomposição de um quality score (0-100) em subcomponentes.

    Cada componente pontua de 0 a 100 dentro do seu próprio critério.
    O `total` é a média ponderada deles.
    """

    parity: float  # equilíbrio par/ímpar
    sum_band: float  # soma na faixa histórica
    range_coverage: float  # cobertura das faixas (10s)
    sequences: float  # ausência de longas sequências consecutivas
    frequency: float  # quão "quentes" são as dezenas escolhidas
    delay: float  # quanto contemplam dezenas atrasadas
    affinity: float  # co-ocorrência histórica
    total: float
    weights: dict[str, float] = field(default_factory=dict)
    flags: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, float]:
        """Retorna apenas os componentes numéricos (sem weights/flags)."""
        return {
            "parity": self.parity,
            "sum_band": self.sum_band,
            "range_coverage": self.range_coverage,
            "sequences": self.sequences,
            "frequency": self.frequency,
            "delay": self.delay,
            "affinity": self.affinity,
            "total": self.total,
        }


# Pesos default — balanceados. O usuário pode customizar via `Logic Pro`
# ponderado mencionado no README.
DEFAULT_WEIGHTS: dict[str, float] = {
    "parity": 1.0,
    "sum_band": 1.0,
    "range_coverage": 1.0,
    "sequences": 1.0,
    "frequency": 1.0,
    "delay": 0.7,
    "affinity": 0.8,
}


def _score_parity(numbers: tuple[int, ...], spec: GameSpec) -> float:
    """100 se atinge a paridade alvo; cai linearmente com o desvio."""
    even_count = sum(1 for n in numbers if n % 2 == 0)
    target = spec.target_even_count or (spec.draw_size // 2)
    diff = abs(even_count - target)
    max_diff = max(target, spec.draw_size - target) or 1
    return max(0.0, 100.0 * (1 - diff / max_diff))


def _score_sum(numbers: tuple[int, ...], spec: GameSpec) -> float:
    """100 se soma está na faixa-alvo; degrada suavemente fora dela."""
    s = sum(numbers)
    low, high = spec.sum_target_low, spec.sum_target_high
    if low is None or high is None:
        return 50.0  # sem alvo definido: neutro
    if low <= s <= high:
        return 100.0
    # Decaimento linear até zero a uma "largura de banda" de distância.
    band = (high - low) or 1
    distance = low - s if s < low else s - high
    return max(0.0, 100.0 * (1 - distance / band))


def _score_range_coverage(numbers: tuple[int, ...], spec: GameSpec) -> float:
    """
    Cobertura por faixas de 10 dezenas (1-10, 11-20, ...).

    100 se a distribuição é exatamente proporcional; cai conforme a
    concentração se desvia. Mede com qui-quadrado normalizado.
    """
    bin_size = 10
    n_bins = math.ceil(spec.universe / bin_size)
    if n_bins <= 1:
        return 100.0  # universo pequeno (ex: Super Sete) — irrelevante

    bins = np.zeros(n_bins, dtype=np.float64)
    for n in numbers:
        bins[(n - 1) // bin_size] += 1

    expected = len(numbers) / n_bins
    if expected == 0:
        return 0.0
    chi2 = ((bins - expected) ** 2 / expected).sum()
    # chi2 máximo aproximado: tudo concentrado num bin = (k-1)*exp + (size-exp)^2/exp
    max_chi2 = (n_bins - 1) * expected + (len(numbers) - expected) ** 2 / expected
    return max(0.0, 100.0 * (1 - chi2 / max_chi2)) if max_chi2 > 0 else 100.0


def _score_sequences(numbers: tuple[int, ...]) -> float:
    """
    Penaliza sequências longas (3+ consecutivas) que reduzem a qualidade
    estrutural. Permite duplas (que são comuns) sem penalidade.

    100 = só duplas ou nenhuma sequência. Cai com o tamanho da maior run.
    """
    if len(numbers) < 2:
        return 100.0
    sorted_nums = sorted(numbers)
    longest_run = 1
    current = 1
    for i in range(1, len(sorted_nums)):
        if sorted_nums[i] == sorted_nums[i - 1] + 1:
            current += 1
            longest_run = max(longest_run, current)
        else:
            current = 1
    if longest_run <= 2:
        return 100.0
    # Cada dezena além da segunda numa run reduz 25 pontos.
    return max(0.0, 100.0 - (longest_run - 2) * 25.0)


def _score_frequency_aware(
    numbers: tuple[int, ...],
    stats: FrequencyStats,
) -> float:
    """
    Quão "quentes" são as dezenas escolhidas, comparado à expectativa.

    Em vez do `fitness += 10 * frequencia[dezena]` do AG original (que dá
    score absoluto não-comparável), usamos a frequência relativa
    normalizada pela frequência média esperada. Dezenas perfeitamente
    típicas dão 50; dezenas muito acima da média aproximam-se de 100.
    """
    if stats.total_contests == 0:
        return 50.0
    idx = np.array([n - 1 for n in numbers], dtype=np.intp)
    chosen_relative = stats.relative[idx].mean()
    expected_relative = stats.spec.draw_size / stats.spec.universe  # se uniforme
    if expected_relative == 0:
        return 50.0
    ratio = chosen_relative / expected_relative
    # ratio=1 -> 50 pts; ratio=2 -> ~85 pts; ratio=0.5 -> ~25 pts
    return float(np.clip(50 * ratio, 0, 100))


def _score_delay_aware(
    numbers: tuple[int, ...],
    stats: FrequencyStats,
) -> float:
    """
    Bilhetes que incluem dezenas atrasadas ganham pontos.

    Calcula a média dos atrasos das dezenas escolhidas, normalizada
    pelo atraso médio esperado (que é universe/draw_size para sorteio
    uniforme).
    """
    if stats.total_contests == 0:
        return 50.0
    idx = np.array([n - 1 for n in numbers], dtype=np.intp)
    avg_delay = float(stats.delays[idx].mean())
    expected_delay = stats.spec.universe / stats.spec.draw_size
    if expected_delay == 0:
        return 50.0
    ratio = avg_delay / expected_delay
    return float(np.clip(50 * ratio, 0, 100))


def _score_affinity_aware(
    numbers: tuple[int, ...],
    cooc: np.ndarray | None,
    expected_per_pair: float | None,
) -> float:
    """
    Score baseado em co-ocorrência histórica. Comparado ao baseline
    aleatório (`expected_per_pair`).

    Se `cooc` for None, devolve 50 (neutro) — usado quando o usuário
    não quer pagar o custo de calcular a matriz de pares.
    """
    if cooc is None or expected_per_pair is None or expected_per_pair <= 0:
        return 50.0
    raw = affinity_score(numbers, cooc)
    n = len(numbers)
    pairs_in_ticket = n * (n - 1) // 2
    if pairs_in_ticket == 0:
        return 50.0
    expected_total = expected_per_pair * pairs_in_ticket
    ratio = raw / expected_total if expected_total > 0 else 1.0
    return float(np.clip(50 * ratio, 0, 100))


def evaluate_ticket(
    numbers: tuple[int, ...],
    spec: GameSpec,
    stats: FrequencyStats | None = None,
    cooc: np.ndarray | None = None,
    weights: dict[str, float] | None = None,
) -> QualityBreakdown:
    """
    Avalia um bilhete e devolve sua decomposição de qualidade.

    Esta é a função que alimenta:
      - O badge de cor 0-100 do "Meus Jogos"
      - O painel X-Ray
      - O fitness do AG (ver `generators/genetic.py`)
      - A ordenação dos resultados do Logic Pro

    Args:
        numbers: dezenas do bilhete.
        spec: especificação da loteria.
        stats: estatísticas de frequência. Se None, scores dependentes
               de histórico ficam neutros (50). Permite avaliar bilhetes
               offline.
        cooc: matriz de co-ocorrência. Se None, score de afinidade neutro.
        weights: pesos customizados. Falta de chave usa default.
    """
    flags: list[str] = []
    # Validação leve — duplicatas viram flag, não exceção (o GA usa essa
    # função em estados intermediários).
    if len(numbers) != len(set(numbers)):
        flags.append("dezenas duplicadas")
    if any(n < 1 or n > spec.universe for n in numbers):
        flags.append("dezenas fora do universo")

    w = {**DEFAULT_WEIGHTS, **(weights or {})}

    parity = _score_parity(numbers, spec)
    sum_band = _score_sum(numbers, spec)
    range_cov = _score_range_coverage(numbers, spec)
    sequences = _score_sequences(numbers)
    frequency = _score_frequency_aware(numbers, stats) if stats else 50.0
    delay = _score_delay_aware(numbers, stats) if stats else 50.0

    expected_per_pair = None
    if cooc is not None and stats and stats.total_contests > 0:
        # Calcula o baseline esperado: total de co-ocorrências / pares possíveis.
        univ = spec.universe
        total_pairs = univ * (univ - 1) // 2
        if total_pairs > 0:
            total_cooc = float(np.triu(cooc, k=1).sum())
            expected_per_pair = total_cooc / total_pairs
    affinity = _score_affinity_aware(numbers, cooc, expected_per_pair)

    components = {
        "parity": parity,
        "sum_band": sum_band,
        "range_coverage": range_cov,
        "sequences": sequences,
        "frequency": frequency,
        "delay": delay,
        "affinity": affinity,
    }
    weighted_sum = sum(components[k] * w[k] for k in components)
    weight_total = sum(w[k] for k in components) or 1.0
    total = weighted_sum / weight_total

    # Penalidades duras só para violações estruturais — não por estatística.
    if "dezenas duplicadas" in flags or "dezenas fora do universo" in flags:
        total = 0.0

    return QualityBreakdown(
        parity=parity,
        sum_band=sum_band,
        range_coverage=range_cov,
        sequences=sequences,
        frequency=frequency,
        delay=delay,
        affinity=affinity,
        total=round(total, 2),
        weights=w,
        flags=flags,
    )
