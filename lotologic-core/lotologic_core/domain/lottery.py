"""
Entidades de domínio das loterias da CAIXA.

Generalização do conceito de loteria. Onde o AG-LotofacilPreditor
hard-codeava 25/15 e a tabela 5x5 da Lotofácil, aqui parametrizamos
para qualquer loteria via `GameSpec`. Isso permite que o mesmo motor
de análise/geração sirva Mega-Sena, Quina, Lotofácil, etc.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class GameSpec:
    """
    Especificação imutável de uma loteria.

    Atributos:
        key: identificador (ex: "lotofacil", "megasena").
        name: nome de exibição.
        universe: maior dezena sorteável (ex: 25 para Lotofácil, 60 para Mega).
        draw_size: quantas dezenas são sorteadas em cada concurso.
        min_picks: menor número de dezenas que se pode marcar num bilhete.
        max_picks: maior número de dezenas que se pode marcar.
        sum_target_low / sum_target_high: faixa "ideal" da soma das dezenas
            para o quality score. Default: ~ (universe*draw_size*0.40,
            universe*draw_size*0.55), que aproxima a faixa observada
            historicamente em todas as loterias da CAIXA.
        grid_rows / grid_cols: forma da cartela visual oficial — usada na
            análise de vizinhança/diagonal. None se a loteria não tiver
            grade quadrada (ex: Super Sete, Loteca).
        target_even_count: paridade ideal observada (default: draw_size//2).
    """

    key: str
    name: str
    universe: int
    draw_size: int
    min_picks: int
    max_picks: int
    sum_target_low: Optional[int] = None
    sum_target_high: Optional[int] = None
    grid_rows: Optional[int] = None
    grid_cols: Optional[int] = None
    target_even_count: Optional[int] = None

    def __post_init__(self):
        # Validação preguiçosa via early return de erros.
        if self.universe <= 0 or self.draw_size <= 0:
            raise ValueError(f"GameSpec {self.key}: universe e draw_size devem ser > 0")
        if self.draw_size > self.universe:
            raise ValueError(f"GameSpec {self.key}: draw_size > universe")
        if self.min_picks > self.max_picks:
            raise ValueError(f"GameSpec {self.key}: min_picks > max_picks")
        if self.max_picks > self.universe:
            raise ValueError(f"GameSpec {self.key}: max_picks > universe")

        # Defaults derivados — preenchidos via object.__setattr__ porque o
        # dataclass é frozen.
        if self.sum_target_low is None:
            low = int(self.universe * self.draw_size * 0.40)
            object.__setattr__(self, "sum_target_low", low)
        if self.sum_target_high is None:
            high = int(self.universe * self.draw_size * 0.55)
            object.__setattr__(self, "sum_target_high", high)
        if self.target_even_count is None:
            object.__setattr__(self, "target_even_count", self.draw_size // 2)


# ---------------------------------------------------------------------------
# Catálogo das 9 loterias numéricas suportadas pelo LotoLogic.
# Valores: cartelas oficiais da CAIXA (julho/2025). Faixa de soma calibrada
# pelo histórico real (não pelo default 0.40-0.55, que é fallback).
# ---------------------------------------------------------------------------

LOTERIAS: dict[str, GameSpec] = {
    "megasena": GameSpec(
        key="megasena",
        name="Mega-Sena",
        universe=60,
        draw_size=6,
        min_picks=6,
        max_picks=20,
        sum_target_low=140,  # observado historicamente
        sum_target_high=240,
        grid_rows=6,
        grid_cols=10,
    ),
    "lotofacil": GameSpec(
        key="lotofacil",
        name="Lotofácil",
        universe=25,
        draw_size=15,
        min_picks=15,
        max_picks=20,
        sum_target_low=190,  # mesmo critério usado no AG da Camila
        sum_target_high=260,
        grid_rows=5,
        grid_cols=5,
        target_even_count=7,  # 7 pares / 8 ímpares (literatura específica)
    ),
    "quina": GameSpec(
        key="quina",
        name="Quina",
        universe=80,
        draw_size=5,
        min_picks=5,
        max_picks=15,
        sum_target_low=150,
        sum_target_high=255,
        grid_rows=8,
        grid_cols=10,
    ),
    "lotomania": GameSpec(
        key="lotomania",
        name="Lotomania",
        universe=100,  # 00 a 99 — tratamos 100 como "0"
        draw_size=20,
        min_picks=50,
        max_picks=50,
        sum_target_low=850,
        sum_target_high=1150,
        grid_rows=10,
        grid_cols=10,
    ),
    "timemania": GameSpec(
        key="timemania",
        name="Timemania",
        universe=80,
        draw_size=7,
        min_picks=10,
        max_picks=10,
        sum_target_low=240,
        sum_target_high=340,
        grid_rows=8,
        grid_cols=10,
    ),
    "duplasena": GameSpec(
        key="duplasena",
        name="Dupla Sena",
        universe=50,
        draw_size=6,
        min_picks=6,
        max_picks=15,
        sum_target_low=120,
        sum_target_high=200,
        grid_rows=5,
        grid_cols=10,
    ),
    "diadesorte": GameSpec(
        key="diadesorte",
        name="Dia de Sorte",
        universe=31,
        draw_size=7,
        min_picks=7,
        max_picks=15,
        sum_target_low=85,
        sum_target_high=140,
        # Sem grid quadrado: cartela é 1-31 em linha.
    ),
    "supersete": GameSpec(
        key="supersete",
        name="Super Sete",
        # Modelagem: 7 colunas, dígitos 0-9 em cada. Codificamos como um
        # universo virtual de 70 dezenas: dezena = coluna * 10 + dígito
        # (col 1 → 10..19, col 2 → 20..29, ..., col 7 → 70..79; usamos 0..69
        # internamente). Permite reaproveitar todo o motor numérico genérico.
        universe=70,
        draw_size=7,
        min_picks=7,
        max_picks=21,
        sum_target_low=210,
        sum_target_high=280,
    ),
    "maismilionaria": GameSpec(
        key="maismilionaria",
        name="+Milionária",
        universe=50,
        draw_size=6,
        min_picks=6,
        max_picks=12,
        sum_target_low=120,
        sum_target_high=200,
        grid_rows=5,
        grid_cols=10,
    ),
}


def get_spec(key: str) -> GameSpec:
    """Retorna o GameSpec da loteria. Lança KeyError com mensagem útil."""
    if key not in LOTERIAS:
        raise KeyError(
            f"Loteria '{key}' desconhecida. "
            f"Disponíveis: {sorted(LOTERIAS.keys())}"
        )
    return LOTERIAS[key]


@dataclass(frozen=True)
class Draw:
    """
    Um concurso realizado: dezenas sorteadas + metadados.

    Os números ficam ordenados crescentemente — a ordem de sorteio é
    irrelevante para análise estatística (fonte: Caixa publica os
    dois formatos, e o LotoLogic descarta a ordem).
    """

    contest: int
    game: str
    numbers: tuple[int, ...]
    draw_date: Optional[date] = None
    accumulated: bool = False

    def __post_init__(self):
        if len(self.numbers) != len(set(self.numbers)):
            raise ValueError(
                f"Draw {self.game}#{self.contest}: dezenas duplicadas {self.numbers}"
            )
        # Garante ordenação para igualdade estrutural.
        sorted_nums = tuple(sorted(self.numbers))
        if sorted_nums != self.numbers:
            object.__setattr__(self, "numbers", sorted_nums)


@dataclass(frozen=True)
class Ticket:
    """Um bilhete de aposta (não necessariamente sorteado ainda)."""

    game: str
    numbers: tuple[int, ...]
    strategy: str = "manual"
    extra_fields: dict = field(default_factory=dict)
    """extra_fields: campos especiais como 'mes_sorte', 'time_coracao', 'trevos'."""

    def __post_init__(self):
        if len(self.numbers) != len(set(self.numbers)):
            raise ValueError(f"Ticket: dezenas duplicadas {self.numbers}")
        sorted_nums = tuple(sorted(self.numbers))
        if sorted_nums != self.numbers:
            object.__setattr__(self, "numbers", sorted_nums)
