# lotologic-core

> Núcleo lógico aprimorado para o app **LotoLogic** ([dantetesta/LotoLogic](https://github.com/dantetesta/LotoLogic)).

Pacote Python independente que implementa motor de análise estatística e geração de jogos para as **9 loterias numéricas da CAIXA**: Mega-Sena, Lotofácil, Quina, Lotomania, Timemania, Dupla Sena, Dia de Sorte, Super Sete e +Milionária.

Construído como reescrita corrigida e generalizada do AG-LotofacilPreditor de Camila Florão Barcellos e Bernardo Tomasi (UFPel), com bugs identificados, corrigidos e cobertos por testes regressivos. Veja [`BUGS_FOUND.md`](./BUGS_FOUND.md).

## Por que existe

O app LotoLogic (Tauri/React, fechado) descreve no README 9 módulos com lógica estatística — Dashboard, Concursos, Gerador, Logic Pro, Assistente IA, Meus Jogos, SuperLab, Desdobramento e Configurações. Este pacote implementa o **núcleo lógico** desses módulos como biblioteca Python pura, podendo ser:

- Usado standalone via CLI (`lotologic-core ga lotofacil`)
- Integrado no app Tauri via `subprocess` ou ponte PyO3
- Reusado em qualquer projeto Python que precise de análise/geração de loteria

## Instalação

```bash
git clone <url> lotologic-core
cd lotologic-core
pip install -e .
```

Apenas uma dependência: `numpy>=1.24`.

## Quickstart

### Como biblioteca

```python
from lotologic_core import (
    get_spec, CaixaApiClient,
    compute_frequency_stats, cooccurrence_matrix,
    TicketGA, GAConfig,
    evaluate_ticket,
)

# 1. Especifica a loteria
spec = get_spec("lotofacil")

# 2. Carrega histórico (API real ou histórico próprio)
client = CaixaApiClient()
history = list(client.iter_history("lotofacil", since=3000))

# 3. Calcula estatísticas
stats = compute_frequency_stats(history, spec)
cooc = cooccurrence_matrix(history, spec)

# 4. Roda Algoritmo Genético com fitness multi-objetivo
ga = TicketGA(spec, stats, n_numbers=15, cooc=cooc,
              config=GAConfig(population_size=100, n_generations=200, seed=42))
result = ga.run()

print(result.best_ticket)              # bilhete otimizado
print(result.best_score)               # 0..100
print(result.best_breakdown.as_dict()) # raio-X dos 7 componentes
```

### Como CLI

```bash
# Listar loterias suportadas
lotologic-core list

# Estatísticas (modo demo, offline)
lotologic-core stats megasena --history demo

# Gerar 5 bilhetes com estratégia híbrida
lotologic-core generate lotofacil --strategy hybrid --count 5

# Algoritmo genético
lotologic-core ga lotofacil --history demo --pop 100 --gen 200

# Backtest cronológico (sem look-ahead)
lotologic-core backtest megasena --strategy delayed --history demo

# Desdobramento (covering design C(v,k,t))
lotologic-core covering --pool 1,3,5,7,9,11,13,15,17,19 --k 6 --t 4

# Otimização de portfólio (SuperLab)
lotologic-core pareto megasena --size 5 --history demo
```

> **Nota:** `--history demo` usa concursos sintéticos (offline). Sem essa flag, busca dados reais da [API pública da Caixa](https://loteriascaixa-api.herokuapp.com/api/) — mesma fonte usada pelo workflow oficial do LotoLogic.

## Os 9 módulos do LotoLogic — onde cada um vive aqui

| Módulo do app             | Implementação no pacote                                              |
|---------------------------|----------------------------------------------------------------------|
| Dashboard                 | `analysis.frequency` + `analysis.pairs`                              |
| Concursos                 | `data.caixa_api.CaixaApiClient`                                      |
| Gerador (7 estratégias)   | `generators.strategies` — `random/historical/recent/delayed/balanced/hybrid/affinity` |
| Logic Pro (IA)            | `generators.genetic.TicketGA` + `analysis.quality_score`             |
| Assistente IA             | `analysis.quality_score.evaluate_ticket` (raio-X em 7 componentes)   |
| Meus Jogos                | `domain.lottery.Ticket` + `backtest.runner`                          |
| SuperLab (otimizar combo) | `generators.pareto.optimize_portfolio` (3 objetivos)                 |
| Desdobramento             | `generators.covering.greedy_covering` (covering design C(v,k,t))     |
| Configurações             | `domain.lottery.LOTERIAS` (9 specs parametrizáveis)                  |

## Aprimoramentos vs. AG-LotofacilPreditor original

Veja [`BUGS_FOUND.md`](./BUGS_FOUND.md) para análise detalhada. Resumo:

| # | Bug original                                 | Correção neste pacote                              |
|---|----------------------------------------------|----------------------------------------------------|
| 1 | Crossover de ponto único produz duplicatas   | Subset Crossover (união - interseção + setdiff)    |
| 2 | Mutação por swap é no-op (bilhete é conjunto)| Mutação substitutiva (in→out, out→in)              |
| 3 | Fitness destrutivo (zera em violação soft)   | Penalidade gradual + seleção por torneio (não roleta) |
| 4 | Tabela de frequência hard-coded (10 sorteios)| `compute_frequency_stats` vetorizado, qualquer N    |
| 5 | "Distância mínima" telescópica               | `range_coverage` por qui-quadrado em buckets        |

Hard-codes 25/15 e tabela 5×5 da Lotofácil → `GameSpec` parametrizado para todas as 9 loterias.
Loops `for` em Java → operações vetorizadas em NumPy (10–100× mais rápido).

## Testes

```bash
pytest -v
```

A suíte inclui testes regressivos específicos para cada bug corrigido (`TestGABugFixes`) e teste de convergência (`TestGAConvergence::test_converges_better_than_random`).

```
21 passed in 2.03s
```

## Arquitetura

```
lotologic_core/
├── domain/         # GameSpec, Draw, Ticket — entidades imutáveis
├── data/           # Cliente da API da Caixa (urllib, sem deps)
├── analysis/       # Frequência, pares, quality score (ex-fitness)
├── generators/     # 7 estratégias + AG + covering + Pareto
├── backtest/       # Validação cronológica honesta (sem look-ahead)
└── cli.py          # Argparse multi-comando
```

Clean Architecture: `domain` não importa nada, `analysis` importa só `domain`, `generators` importam `analysis`, etc. Permite trocar API da Caixa, formato de quality score ou estratégia sem tocar nas camadas adjacentes.

## Limitações honestas

- **Loterias são sorteios uniformes independentes.** Nenhum motor (este, o original, ou outros) consegue prever resultados. Este pacote ajuda a (a) entender o histórico, (b) gerar bilhetes que satisfazem critérios estatísticos do *passado*, e (c) backtestar estratégias de forma honesta. **Não há garantia de retorno financeiro.**
- O backtest mostra que estratégias historicamente "informadas" tendem a performar dentro da margem de erro da expectativa uniforme (i.e., próximo de `n_picked * draw_size / universe`). Isso é o resultado correto.
- Super Sete usa modelagem virtual (universo 70 = 7 col × 10 dígitos). Estratégias multi-coluna específicas ficaram para versões futuras.

## Licença

MIT.
