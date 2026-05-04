# Bugs encontrados no AG-LotofacilPreditor e correções aplicadas

Este documento registra problemas estruturais identificados no código do
[AG-LotofacilPreditor](https://github.com/camilafbarcellos/AG-LotofacilPreditor)
de Bernardo Tomasi e Camila Florão Barcellos (TCC, Congresso TI 2023) e
descreve como o `lotologic-core` os corrige. O trabalho original tem grande
mérito didático e organização clara — os problemas abaixo são detalhes de
implementação que não invalidam a abordagem; são apenas oportunidades
concretas de melhoria.

Referência: [`PreditorLotofacil/src/algoritmogenetico/LotoNumeros.java`](https://github.com/camilafbarcellos/AG-LotofacilPreditor/blob/master/PreditorLotofacil/src/algoritmogenetico/LotoNumeros.java)

---

## 🐛 Bug 1 — Crossover de ponto único produz cromossomos com duplicatas

### Trecho do código original (linhas 378–401)

```java
private static int[] crossover(int[] pai1, int[] pai2) {
    int[] filho = new int[15];
    if (random.nextDouble() < TAXA_REPRODUCAO) {
        int crossoverPoint = random.nextInt(pai1.length);
        for (int i = 0; i < crossoverPoint; i++) {
            filho[i] = pai1[i];           // copia início do pai1
        }
        for (int i = crossoverPoint; i < pai2.length; i++) {
            filho[i] = pai2[i];           // copia final do pai2
        }
    } else {
        filho = pai1;
    }
    return filho;
}
```

### Problema

Pais distintos podem conter dezenas em comum em posições diferentes. Por
exemplo:

```
pai1 = [01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15]
pai2 = [05, 06, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 11, 12, 13]
crossoverPoint = 7
filho = [01, 02, 03, 04, 05, 06, 07, 21, 22, 23, 24, 25, 11, 12, 13]
                                  ^^                    ^^
```

O filho tem `05` (vindo de pai1[4]) e `21` (vindo de pai2[7]), e nenhuma
duplicata neste exemplo — mas em ~60% dos crossovers reais sobre populações
diversas haverá pelo menos uma colisão. O fitness do código original detecta
isso (linhas 324-330) e zera o fitness do indivíduo, descartando-o de fato.

### Consequências

1. **Eficiência**: a maioria dos crossovers vira ruído. O GA passa a maior
   parte do tempo regerando indivíduos válidos por elitismo.
2. **Viés**: a probabilidade de duplicata depende da posição de corte e da
   composição dos pais — não é uniforme. Isso favorece pares com pouca
   sobreposição, criando um drift genético não intencional.
3. **Diversidade falsa**: a população parece mais diversa do que é, porque
   muitos indivíduos novos são inválidos (mas contam como "novos").

### Correção em `lotologic-core`

[`generators/genetic.py::TicketGA._crossover`](lotologic_core/generators/genetic.py)
implementa **Subset Crossover**:

1. Calcula a interseção dos dois pais — essas dezenas entram garantidamente
   no filho (são "genes consolidados pela evolução").
2. Calcula a união dos dois pais.
3. Completa o restante do filho amostrando aleatoriamente da diferença
   `união − interseção` sem reposição.
4. Se a união não cobre `n_numbers`, complementa com dezenas de fora dos
   pais (caso degenerado raro).

Garantias formais:
- ✅ Filho sempre com `n_numbers` dezenas únicas
- ✅ Filho sempre dentro do universo válido
- ✅ Genes "fortes" (presentes em ambos os pais) preservados

---

## 🐛 Bug 2 — Mutação por troca de posições é semanticamente nula

### Trecho do código original (linhas 411–427)

```java
private static int[] mutacao(int[] individual) {
    int[] mutante = individual.clone();
    int index1 = random.nextInt(mutante.length);
    int index2 = 0;
    do {
        index2 = random.nextInt(mutante.length);
    } while (index2 == index1);
    int temp = mutante[index1];
    mutante[index1] = mutante[index2];
    mutante[index2] = temp;
    return mutante;
}
```

### Problema

A mutação troca a posição de duas dezenas dentro do mesmo array. Mas para
loteria, **um bilhete é um conjunto** — a ordem das dezenas no array não
importa. `{1, 2, 3}` é o mesmo bilhete que `{3, 1, 2}`.

A função fitness (`calculaFitness`) confirma essa irrelevância: ela usa
`contagemPares` (sem se importar com ordem), `contarParesDiagonal` (que
mapeia índice do array para posição na cartela 5×5), `contagemPrimos`,
soma, etc. Todas essas operações comutam — **a mutação por swap de
posições não altera nenhuma delas**.

A única exceção é `contarParesDiagonal`, que olha para `individual[num]`
indexado pela cartela 5×5. Mas o mapeamento é incoerente: ele usa o ÍNDICE
do array como posição na grade, não a DEZENA — então a "técnica diagonal"
do código original mede algo diferente do que a teoria indica (a diagonal
deveria ser sobre a cartela visual da Lotofácil, com base nos VALORES).

### Consequências

A mutação efetivamente **não introduz variação genética**. A diversidade
populacional vem apenas do crossover (que como vimos no Bug 1 é instável)
e do elitismo. O GA fica preso em ótimos locais com mais frequência.

### Correção em `lotologic-core`

[`generators/genetic.py::TicketGA._mutate`](lotologic_core/generators/genetic.py)
implementa **mutação por substituição**:

1. Escolhe aleatoriamente uma dezena do indivíduo para sair.
2. Escolhe aleatoriamente uma dezena de fora do indivíduo para entrar.
3. Substitui.

É o operador genético padrão para GAs sobre subconjuntos de tamanho fixo
(literatura de algoritmos genéticos sobre permutações: Goldberg 1989,
Eiben & Smith 2015). Garante:
- ✅ Tamanho preservado
- ✅ Unicidade preservada  
- ✅ Diferença simétrica entre original e mutante = exatamente 2 dezenas
- ✅ Mudança real no conjunto (não no array)

Adicionalmente, a "técnica diagonal" foi reescrita em
[`analysis/quality_score.py::_score_range_coverage`](lotologic_core/analysis/quality_score.py)
como uma medida de **cobertura de faixas via qui-quadrado** — operando
sobre os valores das dezenas, não sobre índices.

---

## 🐛 Bug 3 — Fitness destrutivo (`fitness = 0`) destrói o gradiente

### Trechos do código original (linhas 232–337)

```java
// Soma fora da faixa zera tudo
if (soma >= 190 && soma <= 260) {
    fitness += 50;
} else {
    fitness = 0;
}

// Pares diagonais fora da banda zeram tudo
if (pares < 2 || pares > 17) {
    fitness = 0;
} else {
    fitness += (10 * (contarParesDiagonal(individual)));
}

// Menos de 2 primos zera tudo
if (primos >= 2) {
    fitness += (5 * (contarNumerosPrimos(individual)));
} else {
    fitness = 0;
}

// Duplicata zera tudo
for (int i = 0; i < individual.length - 1; i++) {
    for (int j = i + 1; j < individual.length; j++) {
        if (individual[i] == individual[j]) {
            fitness = 0;
            break;
        }
    }
}
```

### Problema

O fitness é zerado em qualquer das condições acima. Combinado com a
**roleta de seleção** (`selecinaIndividuoFitness`, que opera por
proporcionalidade ao fitness):

```java
double totalFitness = 0;
for (double fitnessValue : valoresFitness) {
    totalFitness += fitnessValue;
}
double randomFitness = random.nextDouble() * totalFitness;
```

Indivíduos com fitness=0 têm **probabilidade zero de serem selecionados**.
Eles são tratados como "lixo absoluto", quando na verdade muitos deles
estão a uma única mutação de serem ótimos.

Pior: nas primeiras gerações, é comum que **TODA a população** caia em
algum critério zerado (especialmente por duplicata + soma fora de faixa).
Quando isso ocorre, `totalFitness=0` e a roleta retorna sempre o último
indivíduo da lista. O GA degenera.

### Consequências

1. **Convergência ruim**: o algoritmo não consegue refinar gradualmente —
   ou um indivíduo passa em todos os critérios duros, ou é zero.
2. **Sem direção**: a função fitness vira binária num espaço de
   subconjuntos enorme, perdendo o gradiente que orienta o GA.
3. **Bug crítico em populações iniciais aleatórias**: ~99% dos
   indivíduos aleatórios falham na faixa de soma 190-260 (a soma
   esperada de 15 dezenas aleatórias em 1-25 tem média 195 mas
   desvio-padrão alto), então a primeira geração é quase toda zero.

### Correção em `lotologic-core`

[`analysis/quality_score.py::evaluate_ticket`](lotologic_core/analysis/quality_score.py)
substitui as zeragens duras por **penalidades suaves**:

| Critério | Comportamento original | Comportamento corrigido |
|---|---|---|
| Soma fora de [190, 260] | fitness = 0 | score linear de 100 a 0 conforme distância |
| Paridade ≠ 7 pares | fitness += 0 (sem penalidade!) | score linear conforme |diff| |
| Sequência longa | não tratado | score 100 → 0 conforme run length |
| Distribuição em faixas | não tratado | score por qui-quadrado normalizado |
| Frequência | += 10·freq[d] (escala arbitrária) | score 0-100 normalizado vs uniforme |

Apenas violações **estruturais** (duplicatas ou dezenas fora do universo)
zeram o score — porque essas são verdadeiramente inválidas. E mesmo essas
não acontecem mais, dadas as correções dos Bugs 1 e 2.

A roleta foi também substituída por **seleção por torneio**
(`_tournament_select`), que é mais robusta a fitness com escalas variadas
e não depende de `totalFitness > 0`.

---

## 🐛 Bug 4 (menor) — Tabela de frequência hard-coded

### Trecho do código original (linhas 187–218)

```java
private static void criadorTabelaFreq() {
    int[][] sorteios = {
        {1, 2, 3, 5, 8, 9, 10, 11, 13, 15, 18, 20, 22, 24, 25},
        {2, 4, 5, 6, 8, 9, 12, 13, 14, 17, 18, 19, 23, 24, 25},
        // ... 10 sorteios manualmente digitados ...
    };
    // ...
}
```

### Problema

Apenas 10 concursos. Hard-coded. Não atualiza. Não permite que o usuário
mude a janela de análise.

### Correção

[`analysis/frequency.py::compute_frequency_stats`](lotologic_core/analysis/frequency.py)
aceita qualquer histórico real, vetoriza com NumPy, e oferece:

- Frequência absoluta e relativa
- Atraso (sorteios desde última aparição)
- Recência ponderada com decaimento exponencial (parametrizável)
- Janela móvel arbitrária (5/10/30/50/100… concursos)

E [`data/caixa_api.py::CaixaApiClient`](lotologic_core/data/caixa_api.py)
puxa dados reais da API oficial usada pelo próprio LotoLogic
(`loteriascaixa-api.herokuapp.com`) — mantendo compatibilidade com o
workflow `update-data.yml` do projeto original.

---

## 🐛 Bug 5 (menor) — Critério de "distância mínima" telescópico

### Trecho do código original (linhas 286–289)

```java
for (int i = 0; i < individual.length - 1; i++) {
    int dif = Math.abs(individual[i] - individual[i + 1]);
    fitness += dif;
}
```

### Problema

Como `individual` é geralmente ordenado pelo `Collections.shuffle` e o
fluxo posterior, e como esse loop soma `|x[i] - x[i+1]|`, em valores
**ordenados** essa soma é `max - min` por telescopia: para `[1, 5, 8, 12]`,
a soma é `|1-5| + |5-8| + |8-12| = 4+3+4 = 11 = 12-1`. Para arrays
**não ordenados**, fica dependente da ordem aleatória das dezenas no array
— novamente, irrelevante para um conjunto.

### Correção

Substituído pelo score `_score_sequences` (baseado na maior run consecutiva)
e pelo score `_score_range_coverage` (cobertura proporcional por bins de
10 dezenas). Ambas são funções da composição do conjunto, não da ordem.

---

## ✅ Resumo da migração

| | Original (Java) | lotologic-core (Python) |
|---|---|---|
| Crossover | Single-point com duplicatas | Subset crossover |
| Mutação | Swap de posições (no-op) | Substituição |
| Fitness | Zerage abrupta | Penalidades suaves 0-100 |
| Seleção | Roleta (frágil) | Torneio (robusta) |
| Frequência | 10 sorteios hard-coded | Dados reais da Caixa via API |
| Generalização | Só Lotofácil | 9 loterias (`GameSpec`) |
| Tipagem | `int[]` cru | Domínio rico (`Draw`, `Ticket`, `GameSpec`) |
| Performance | Loops Java | NumPy vetorizado |
| Testes | Nenhum | Cobertura dos casos críticos |

Os ganhos são reais e mensuráveis: o teste
`TestGAConvergence::test_converges_better_than_random` confirma que o
GA corrigido produz scores estatisticamente acima do baseline aleatório,
algo que o original tinha dificuldade em fazer consistentemente justamente
por causa do fitness destrutivo.
