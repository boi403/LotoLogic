<div align="center">
  <img src="https://lotologic.com.br/logo-lotologic.png" width="220" alt="LotoLogic" />

  <h1>LotoLogic — Manual Completo</h1>

  <p><strong>O laboratório de análise de loterias da CAIXA mais completo para apostadores sérios.</strong><br/>
  Dados reais · Algoritmos profissionais · Inteligência Artificial · 100% local</p>

  <img src="https://img.shields.io/badge/versão-4.2.8-blue?style=flat-square" />
  <img src="https://img.shields.io/badge/plataforma-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square" />
  <img src="https://img.shields.io/badge/licença-MIT-green?style=flat-square" />
</div>

---

## 📥 Download

<div align="center">
  <img src="https://lotologic.com.br/icone-app.png" width="80" alt="LotoLogic App" />
</div>

<br/>

| Plataforma | Instalador | Tipo |
|---|---|---|
| 🪟 **Windows 10/11** | [LotoLogic_4.2.8_x64-setup.exe](https://github.com/dantetesta/LotoLogic/releases/download/v4.2.8/LotoLogic_4.2.8_x64-setup.exe) | Setup (recomendado) |
| 🪟 **Windows 10/11** | [LotoLogic_4.2.8_x64_en-US.msi](https://github.com/dantetesta/LotoLogic/releases/download/v4.2.8/LotoLogic_4.2.8_x64_en-US.msi) | MSI |
| 🍎 **macOS Apple Silicon** (M1/M2/M3/M4) | [LotoLogic_4.2.8_aarch64.dmg](https://github.com/dantetesta/LotoLogic/releases/download/v4.2.8/LotoLogic_4.2.8_aarch64.dmg) | DMG |
| 🍎 **macOS Intel** | [LotoLogic_4.2.8_x64.dmg](https://github.com/dantetesta/LotoLogic/releases/download/v4.2.8/LotoLogic_4.2.8_x64.dmg) | DMG |
| 🐧 **Linux** (Ubuntu, Debian, Mint...) | [LotoLogic_4.2.8_amd64.deb](https://github.com/dantetesta/LotoLogic/releases/download/v4.2.8/LotoLogic_4.2.8_amd64.deb) | .deb |
| 🐧 **Linux** (qualquer distribuição) | [LotoLogic_4.2.8_amd64.AppImage](https://github.com/dantetesta/LotoLogic/releases/download/v4.2.8/LotoLogic_4.2.8_amd64.AppImage) | AppImage |

> 💡 **Mac:** No menu Apple → "Sobre este Mac" — se aparecer "Apple M..." baixe Silicon. Se aparecer "Intel" baixe a versão Intel.
>
> 🐧 **Linux AppImage:** `chmod +x LotoLogic_4.2.8_amd64.AppImage && ./LotoLogic_4.2.8_amd64.AppImage`

---

## ⚠️ Solução de Problemas na Instalação

### macOS — "LotoLogic.app está danificado e não pode ser aberto"

Esse erro é causado pelo Gatekeeper do macOS porque o app não possui assinatura paga da Apple. É seguro ignorar. Para resolver:

**1. Remova o atributo de quarentena antes de instalar:**

```bash
xattr -cr ~/Downloads/LotoLogic_4.2.8_aarch64.dmg
```

Depois abra o DMG normalmente e arraste para Applications.

**2. Ou, se já arrastou para Applications:**

```bash
xattr -cr /Applications/LotoLogic.app
```

**3. Alternativa visual (sem Terminal):**
- Clique com o botão **direito** no app → **Abrir** → confirmar **Abrir** no diálogo

---

### Windows — "Windows protegeu seu PC" (SmartScreen)

Clique em **Mais informações** → **Executar assim mesmo**.

---

### Linux AppImage — permissão de execução

```bash
chmod +x LotoLogic_4.2.8_amd64.AppImage
./LotoLogic_4.2.8_amd64.AppImage
```

---

## 🎰 Loterias Suportadas

Mega-Sena · Lotofácil · Quina · Lotomania · Timemania · Dupla Sena · Dia de Sorte · Super Sete · +Milionária · Loteca · Loteria Federal

---

## 📖 O que é o LotoLogic?

Se você já aposta nas loterias da CAIXA e quer **entender melhor os dados históricos** antes de escolher suas dezenas, o LotoLogic foi feito para você.

O app organiza e analisa o histórico completo de **mais de 23.261 concursos** entre as 9 loterias suportadas — tudo armazenado localmente no seu computador, sem internet, sem mensalidade, sem cadastro.

**O que o LotoLogic faz:**
- Mostra quais dezenas saíram mais ou menos vezes em cada loteria
- Identifica padrões de atraso, frequência e distribuição nos sorteios históricos
- Gera combinações com base em diferentes critérios matemáticos e estatísticos
- Permite organizar, salvar e acompanhar seus próprios jogos
- Conta com uma IA para tirar dúvidas sobre as análises

**O que o LotoLogic NÃO faz:**
- Não prevê resultados futuros — nenhum software consegue isso
- Não garante lucro ou premiação — loterias são jogos de azar por natureza
- Não tem acesso à sua conta da CAIXA ou realiza apostas automáticas

> O LotoLogic é uma ferramenta de análise. As decisões de aposta são sempre suas.

Tudo roda **100% no seu computador** — sem servidores externos. Seus dados nunca saem da sua máquina.

---

## 🧩 Manual Completo — Todos os Módulos

---

### 🏠 1. Dashboard — Painel de Controle

O Dashboard é a tela inicial do LotoLogic. É onde você tem uma visão geral rápida de tudo que está acontecendo.

**O que você encontra aqui:**

- **Sincronização rápida** — Um botão para sincronizar todas as loterias habilitadas de uma vez, baixando apenas os concursos que ainda não estão no seu banco de dados.
- **Seletor de período** — Filtre as estatísticas pelos últimos 5, 10, 30, 50 ou 100 concursos para ver tendências recentes ou históricas.
- **Top 10 mais frequentes** — Gráfico de barras mostrando as 10 dezenas que mais saíram no período selecionado.
- **Top 10 mais atrasadas** — Gráfico de barras com as 10 dezenas que estão há mais tempo sem aparecer (maior "atraso").
- **Análise de campos especiais** — Para loterias como Timemania, Dia de Sorte e +Milionária, exibe estatísticas dos campos especiais (Times do Coração, Mês da Sorte, Trevos).
- **Importação/exportação de banco** — Botões para fazer backup do banco de dados em SQL ou restaurar a partir de um backup existente.
- **Verificação de integridade** — Mostra a contagem de registros em todas as tabelas do banco para garantir que tudo está correto.

---

### 🔍 2. Concursos — Histórico Completo

Este módulo dá acesso ao histórico completo de todos os sorteios realizados pelas loterias da CAIXA desde o primeiro concurso.

**Funcionalidades:**

- **Busca por número** — Digite o número de qualquer concurso para acessá-lo diretamente.
- **Filtro por data** — Selecione um intervalo de datas para ver apenas os concursos daquele período.
- **Paginação** — Navega pelos concursos em páginas de 20 resultados, com navegação por botões ou teclado.
- **Detalhe completo de cada concurso:**
  - Dezenas sorteadas com indicação da ordem do sorteio
  - Para o Super Sete: visualização em colunas como no bilhete oficial
  - Prêmio total acumulado e valor estimado do próximo concurso
  - Distribuição completa de prêmios por faixa (quadra, quina, sena...)
  - Número de ganhadores por faixa e município de origem
  - Campos especiais: Time do Coração (Timemania), Mês da Sorte (Dia de Sorte), Trevos (+Milionária)
  - Indicação se o concurso acumulou ou houve ganhador
- **Score de qualidade estrutural** — Cada concurso recebe uma pontuação de 0 a 100 baseada em equilíbrio par/ímpar, distribuição por faixas, somas e sequências. Útil para entender padrões nos resultados reais.
- **Verificar meus jogos** — Com um clique, o sistema cruza todos os seus jogos salvos contra o resultado daquele concurso e mostra quantos acertos cada jogo teve.
- **Salvar como jogo** — Salva as dezenas sorteadas como um novo jogo em "Meus Jogos" para análise ou referência.

---

### 🎲 3. Gerador — Geração com 7 Estratégias

O Gerador cria apostas individuais ou portfólios completos com base em diferentes estratégias estatísticas.

**As 7 Estratégias disponíveis:**

| Estratégia | Como funciona |
|---|---|
| **Aleatório Puro** | Sorteio completamente aleatório, sem nenhum viés estatístico. Equivale a deixar o computador escolher sem critério. |
| **Frequência Histórica** | Prioriza as dezenas que mais apareceram em toda a história da loteria. "Quentes de longo prazo." |
| **Frequência Recente** | Foca nos últimos 20–50 concursos. Captura tendências de curto prazo, dezenas "em momento". |
| **Dezenas Atrasadas** | Escolhe prioritariamente dezenas que estão há mais tempo sem aparecer, apostando na "lei do retorno". |
| **Balanceado** | Mistura equilibrada entre dezenas frequentes e atrasadas, evitando extremos em qualquer direção. |
| **Híbrido** | Combina frequência histórica, recência e atraso com pesos configuráveis. O mais personalizável. |
| **Afinidade Histórica** | Analisa quais pares de dezenas apareceram juntos com mais frequência e monta jogos priorizando essas combinações. |

**Outros recursos do Gerador:**
- **Quantidade de dezenas** — Ajuste o número de dezenas por jogo (dentro dos limites de cada loteria).
- **Portfólio** — Gere de 2 a 50 jogos de uma só vez, formando uma "carteira" com custo total calculado automaticamente.
- **Valor da aposta** — Preço exato calculado conforme a tabela oficial da CAIXA, atualizada em julho/2025.
- **Histórico de geração** — Os últimos 20 jogos gerados ficam salvos para consulta rápida.
- **Análise X-Ray** — Clique em qualquer jogo gerado para ver uma análise detalhada: distribuição por faixas, soma total, paridade, sequências e pontuação de qualidade.
- **Campos especiais automáticos** — Para loterias como Dia de Sorte, Timemania e +Milionária, o gerador inclui automaticamente os campos especiais (Mês, Time, Trevos) com base na mesma lógica estatística.
- **Copiar e Salvar** — Copie o jogo para a área de transferência ou salve diretamente em "Meus Jogos" com um clique.

---

### ⚙️ 4. Logic Pro — Motor de Análise Profissional

O Logic Pro (anteriormente LotoCore) é o coração analítico do LotoLogic. É um gerador avançado com mais de 20 algoritmos matemáticos e múltiplos modos de operação.

**Os mais de 20 algoritmos incluem:**
- Análise de frequência ponderada por período
- Recência com decaimento exponencial
- Análise de atraso e probabilidade de retorno
- Otimização de paridade (equilíbrio par/ímpar)
- Cobertura de faixas numéricas (01-10, 11-20, etc.)
- Maximização de entropia (diversidade estatística)
- Análise de gaps (intervalos entre aparições)
- Padrões temporais (dia da semana, mês, sazonalidade)
- Correlação de pares históricos
- Análise posicional (qual posição cada dezena ocupa com mais frequência)
- Score composto multi-critério
- E mais de 10 algoritmos adicionais

**Modos de operação:**

- **Modo Combinado** — Todos os algoritmos selecionados trabalham em conjunto, cada um contribuindo para o score final de cada dezena candidata.
- **Modo Ponderado** — Você define o peso de cada algoritmo com sliders. Um peso maior significa mais influência daquele critério na seleção.
- **Seleção única** — Rode apenas um algoritmo por vez para ver seu resultado isolado.

**Recursos exclusivos:**
- **Filtro por score mínimo** — Apenas jogos que atingem um score mínimo configurável são incluídos no resultado.
- **Profundidade de simulação** — Configure quantas iterações internas o motor realiza antes de apresentar os candidatos.
- **Modo Loop** — Gere automaticamente de 1 a 100 portfólios consecutivos sem intervenção. Útil para explorar o espaço de soluções.
- **10+ presets salvos** — Configurações prontas e otimizadas para diferentes perfis de aposta. Escolha um preset como ponto de partida e ajuste conforme sua estratégia.
- **Análise X-Ray Pipeline** — Visualização passo a passo de como o jogo foi construído: qual algoritmo contribuiu com qual dezena e por quê. Transparência total.
- **Salvar em lote** — Selecione todos os jogos acima de um threshold de qualidade e salve-os de uma vez em "Meus Jogos".
- **Ordenação** — Ordene os resultados por score crescente ou decrescente.

---

### 🤖 5. Assistente IA — Análise por Inteligência Artificial

O Assistente IA integra modelos de linguagem diretamente com o seu banco de dados de loterias, permitindo análises e conversas em linguagem natural.

**Provedores e modelos disponíveis:**

| Provedor | Modelos |
|---|---|
| **OpenAI** | GPT-4o, GPT-4o-mini, GPT-4.1-mini |
| **Google Gemini** | gemini-2.0-flash, gemini-2.5-flash |

**O que o Assistente IA pode fazer:**
- Analisar quais dezenas estão "quentes", "frias" ou "atrasadas" para uma loteria específica
- Sugerir jogos baseados nos dados reais do seu banco de dados local
- Explicar estratégias de apostas: frequência, equilíbrio, dispersão, padrões
- Responder dúvidas sobre probabilidade e como as loterias funcionam
- Gerar gráficos de barras, pizza ou linha com dados históricos
- Apresentar curiosidades: recordes, maiores premiações, fatos raros
- Identificar padrões incomuns nos sorteios mais recentes
- Comparar o desempenho de diferentes estratégias ao longo do tempo

**Como usar:**
1. Configure sua chave de API (OpenAI ou Gemini) em Configurações — ela fica armazenada apenas no seu computador, nunca é enviada para servidores do LotoLogic.
2. Selecione o provedor e modelo desejado.
3. Crie uma nova conversa e faça sua pergunta em português natural.
4. O assistente consultará automaticamente o banco de dados local quando necessário.

**Recursos da interface:**
- **Histórico de conversas ilimitado** — Crie múltiplos chats com diferentes temas e volte a qualquer um deles.
- **Cards de jogos sugeridos** — Quando a IA sugere apostas, elas aparecem como cards visuais com botão de salvar individual.
- **Gráficos interativos** — A IA pode gerar visualizações que aparecem diretamente no chat.
- **Renderização Markdown** — Respostas formatadas com tabelas, listas e destaques para facilitar a leitura.

---

### 💾 6. Meus Jogos — Central de Gestão de Apostas

Meus Jogos é a sua carteira pessoal de apostas. Aqui você gerencia tudo que foi salvo — seja criado pelo Gerador, pelo Logic Pro, pelo Assistente IA ou inserido manualmente.

**Organização e filtros:**
- **Filtros rápidos:** Todos / Favoritos / Apostados
- **Favoritos** — Marque jogos com estrela para encontrá-los mais facilmente.
- **Apostado** — Marque quando efetivamente apostou aquele jogo na loteria. Útil para rastrear o que já foi para o bolão ou casa lotérica.

**Informações por jogo:**
- Dezenas do jogo em bolas numeradas coloridas
- Nome personalizado do jogo
- Estratégia utilizada na geração
- Data de criação
- Valor da aposta calculado automaticamente
- **Score de qualidade 0–100** com badge visual de cor (vermelho, amarelo, verde)

**Valor total da carteira:**
O sistema soma automaticamente o valor de todos os jogos marcados como "Apostado", mostrando o custo total da sua carteira de apostas ativa.

**Análise X-Ray (painel lateral):**
Clique em qualquer jogo para abrir o painel detalhado com:
- Distribuição par/ímpar (quantas dezenas pares vs ímpares)
- Soma total das dezenas e comparação com a faixa ideal histórica
- Distribuição por faixas: quantas dezenas em cada grupo (01–10, 11–20, 21–30, etc.)
- Sequências consecutivas: detecta se há 2, 3 ou mais dezenas seguidas
- Unicidade histórica: verifica se esse jogo exato já foi sorteado alguma vez
- Pontuação detalhada de cada critério de qualidade

**Verificação de resultados:**
- **Verificar no último concurso** — Com um clique, confere todos os seus jogos contra o resultado mais recente e mostra os acertos.
- **Verificar histórico completo** — Abre um painel que mostra todos os concursos em que cada jogo teve acertos, com o detalhamento de quantas dezenas coincidiram em cada um.

**Criação e edição:**
- Crie jogos manualmente escolhendo as dezenas uma a uma.
- Dê nomes personalizados para organizar melhor sua coleção.
- Exclua jogos individualmente ou em lote.

**Exportação:**
- **Copiar tudo** — Copia todos os jogos em texto formatado para a área de transferência.
- **Exportar CSV** — Exporta a lista completa em formato .csv compatível com Excel e planilhas.

---

### 🔬 7. SuperLab — Suite Avançada de Análise

O SuperLab é uma suíte completa de ferramentas de análise estatística profissional. É onde apostadores avançados vão além da geração simples e exploram os dados em profundidade.

**Os 10 módulos do SuperLab:**

#### Analytics
Estatísticas detalhadas de cada dezena individualmente: frequência absoluta e relativa, maior e menor atraso já registrado, atraso atual, última aparição, sequências de aparições consecutivas e média de intervalo entre sorteios.

#### Backtest
Teste qualquer estratégia do Gerador ou do Logic Pro contra o histórico real de concursos. Defina um período de teste, rode a estratégia e veja como ela teria performado nos sorteios passados. Métricas incluem taxa de acerto por faixa, custo total simulado e ROI estimado.

#### Monte Carlo
Simulações probabilísticas com milhares de iterações. Escolha um jogo ou conjunto de dezenas e o sistema simula aleatoriamente N sorteios para estimar as probabilidades de cada faixa de acerto. Útil para entender o risco real de uma estratégia.

#### Pares
Análise completa de co-ocorrências: quais pares de dezenas apareceram juntos com maior e menor frequência. Exibe um mapa de calor das combinações mais e menos prováveis com base no histórico. Essencial para quem usa a estratégia de Afinidade Histórica.

#### Gerar com Filtros
Geração avançada com restrições estatísticas: defina critérios como "pelo menos 3 dezenas com atraso acima de X" ou "soma total entre Y e Z" e o sistema gera apenas jogos que satisfazem todas as condições simultaneamente.

#### Cobertura
Análise de cobertura de portfólio: dado um conjunto de jogos, calcula quantas combinações possíveis do espaço amostral total estão cobertas. Mostra o percentual de cobertura e identifica "zonas descobertas" para otimização.

#### Otimizar (Multi-objetivo)
O otimizador Pareto-ótimo. Gera portfólios balanceando três objetivos simultâneos:
- **Frequência histórica** — prioriza dezenas mais sorteadas
- **Diversidade Jaccard** — maximiza a diferença entre os jogos do portfólio
- **Cobertura de pares** — garante que mais combinações de 2 dezenas estejam representadas

Use os sliders de peso para definir a importância relativa de cada objetivo. O resultado é um portfólio de jogos matematicamente otimizado segundo seus critérios.

#### Probabilidade
Calculadora de probabilidades: mostra a chance exata de acertar cada faixa em cada loteria, com e sem campo especial. Também calcula probabilidades condicionais ("dado que acertei X dezenas, qual a chance de acertar Y?").

#### Comparar
Compare dois ou mais jogos lado a lado: veja as dezenas em comum, as exclusivas de cada um, as diferenças nos scores de qualidade, e a distância estatística entre eles (índice de Jaccard).

#### Estratégias
Guia explicativo completo de cada estratégia disponível no sistema, com exemplos práticos, vantagens, desvantagens e quando usar cada uma. Serve como material de estudo para apostadores que estão começando a usar análise estatística.

---

### 📐 8. Desdobramento — Cobertura Matemática Garantida

O Desdobramento resolve um problema matemático clássico em loterias: **como apostar N dezenas de forma que, se as dezenas vencedoras estiverem entre as suas N escolhidas, você tenha garantia de acertar uma faixa específica?**

**Como funciona:**

O módulo usa o algoritmo **Greedy Covering Design**, que calcula o menor número possível de bilhetes necessários para cobrir matematicamente um nível de acerto.

**Exemplo prático:**
- Você seleciona 10 dezenas que acredita serem fortes para a Mega-Sena.
- Você define como garantia: "quero garantir pelo menos uma quadra se 4 das minhas dezenas saírem".
- O sistema calcula e gera automaticamente o conjunto mínimo de bilhetes (aprox. 24 cartões para esse caso) que cobre todas as combinações possíveis dentro das suas 10 dezenas.

**Configurações disponíveis:**
- **Tamanho do pool:** de N+1 a N+8 dezenas acima do mínimo da loteria (ex: Mega-Sena = 6, então pool de 7 a 14 dezenas)
- **Nível de garantia:** escolha a faixa de acerto que deseja garantir (ex: quina, quadra)
- **Seleção visual de dezenas:** grade interativa para escolher suas dezenas com clique
- **Sugestão automática:** o sistema pode sugerir as melhores dezenas para o pool com base nas estatísticas

**3 Presets rápidos:**
| Preset | Pool | Garantia | Bilhetes |
|---|---|---|---|
| Econômico | 8 dezenas | Quina | ~10 cartões |
| Intermediário | 10 dezenas | Quadra | ~24 cartões |
| Avançado | 12 dezenas | Quadra | ~37 cartões |

**Antes de apostar:**
- O sistema exibe o **custo total estimado** com base na tabela oficial da CAIXA
- Cada bilhete mostra a **soma (Σ)** das dezenas para análise rápida

**Salvar e exportar:**
- **Salvar normal** — Salva todos os bilhetes em "Meus Jogos"
- **Salvar + Apostado** — Salva e já marca como apostado
- **Salvar como Favoritos** — Salva e marca com estrela
- **Copiar tudo** — Copia todos os bilhetes em texto
- **Exportar CSV** — Planilha com todos os bilhetes
- **Exportar JSON** — Formato estruturado para uso em outros sistemas

---

### ⚙️ 9. Configurações — Centro de Controle

A página de Configurações é onde você personaliza e gerencia todos os aspectos do LotoLogic.

#### Gerenciamento de Loterias
- **Habilitar/desabilitar loterias** — Ative apenas as loterias que você joga. Loterias desabilitadas não aparecem nos módulos de análise (mínimo 1 ativa obrigatório).
- **Loteria primária** — Defina qual loteria aparece selecionada por padrão em toda a interface.
- **Contador de concursos** — Veja quantos concursos de cada loteria estão no seu banco de dados.
- **Status de sincronização** — Indicador em tempo real: sincronizando, concluído, erro ou pausado.
- **Verificação individual** — Confira se uma loteria específica está atualizada sem sincronizar todas.

#### Importação de Dados Históricos
- **Importação por loteria** — Baixe e importe o banco histórico completo de cada loteria (até 2.990 concursos) com um clique.
- **Importação em lote** — Selecione múltiplas loterias e importe todas de uma vez com barra de progresso por loteria.
- **Importação de backup** — Restaure um backup `.sql` exportado anteriormente.

#### Tabela de Preços de Apostas
- **Preços atualizados** — Tabela completa com os valores oficiais da CAIXA (reajustados em julho/2025).
- **Edição manual** — Edite qualquer preço individualmente caso a CAIXA faça ajustes futuros. Seus preços customizados são preservados em atualizações do app.
- **Cálculo automático** — Todos os módulos usam essa tabela para exibir o valor correto de cada aposta.

#### Calendário Lunar
- **Importação de dados lunares** — Importe o arquivo de fases lunares 1960–2050 para análises avançadas no Assistente IA.
- Alguns usuários utilizam a correlação entre fases lunares e resultados como critério adicional de análise.

#### Manutenção
- **Limpar cache** — Remove arquivos temporários e força a atualização de banners e dados em cache.
- **Reset de fábrica** — Apaga completamente todos os dados do aplicativo (concursos, jogos salvos, configurações). Requer confirmação dupla. **Irreversível.**

---

## 🔒 Privacidade

O LotoLogic foi desenvolvido com **privacidade por design**:

- ✅ Todos os dados armazenados **100% localmente** via SQLite — nunca na nuvem
- ✅ Nenhuma aposta, estatística ou dado pessoal enviado para servidores externos
- ✅ Chaves de API (OpenAI/Gemini) armazenadas apenas no seu dispositivo
- ✅ Sem conta obrigatória, sem cadastro, sem rastreamento
- ✅ Funciona **offline** após a importação inicial dos dados

---

## 💻 Requisitos do Sistema

| | Windows | macOS | Linux |
|---|---|---|---|
| **Versão mínima** | Windows 10 (x64) | macOS 11 Big Sur | Ubuntu 20.04+ |
| **Arquitetura** | x64 | Apple Silicon ou Intel | x86_64 (amd64) |
| **RAM** | 4 GB | 4 GB | 4 GB |
| **Disco** | ~150 MB + dados | ~150 MB + dados | ~250 MB (AppImage) |
| **Conexão** | Para sincronizar concursos | Para sincronizar concursos | Para sincronizar concursos |

---

## 🚀 Como Instalar

**Windows:**
1. Baixe o `.exe` e execute → siga o assistente de instalação

**macOS:**
1. Baixe o `.dmg` correto para o seu chip
2. Arraste o LotoLogic para a pasta Aplicativos
3. Na primeira abertura: botão direito → Abrir → Abrir mesmo assim

**Linux (.deb):**
```bash
sudo dpkg -i LotoLogic_4.2.8_amd64.deb
```

**Linux (AppImage):**
```bash
chmod +x LotoLogic_4.2.8_amd64.AppImage && ./LotoLogic_4.2.8_amd64.AppImage
```

---

## 📋 Changelog

### v4.2.8
- **Fix tela em branco no Mac Intel** — cores oklch() substituídas por hsl(), target de build alterado para safari14
- **Links da página de Créditos corrigidos** — agora abrem no navegador nativo via comando Tauri
- **Startup lento na segunda abertura** — importação do calendário lunar otimizada com batches
- **Analytics melhorado** — evento `first_install` no onboarding, versão dinâmica, conformidade GA4
- Nova imagem de entrada no onboarding e créditos
- CI/CD agora cria Release automaticamente com todos os instaladores

### v4.2.7
- Site oficial **lotologic.com.br** adicionado à página de Créditos
- Link direto para o **repositório GitHub** nos Créditos
- Página de Créditos redesenhada em grid 2×2 (Site, GitHub, Academy, Telegram)
- Arquivos SQL migrados para GitHub CDN (independente do servidor pessoal)
- Atualização automática dos SQLs via GitHub Actions todo dia às 23h59

### v4.2.6
- **Preços CAIXA 2026** atualizados com reajuste de julho/2025
- Mega-Sena, Lotofácil, Quina, Dupla Sena, Dia de Sorte e Super Sete revisados
- Super Sete: range estendido até 21 dezenas
- Novo **ícone do app** com identidade visual LotoLogic
- Atualização automática de preços em instalações existentes (sem perder customizações)

### v4.2.5
- Rebranding completo: LotoLab → **LotoLogic**, novo logo e ícone
- Menu "Gerador Pro" renomeado para **Logic Pro**
- Nova imagem na tela de entrada e créditos
- Grupo Telegram adicionado na página de Créditos

### v4.2.4
- Fix crítico de importação SQL: **2930 → 2990 concursos** importados corretamente
- Causa: comentários de bloco no SQL eram agrupados com o primeiro INSERT de cada batch

### v4.2.3
- SuperLab: Otimizador Multi-objetivo completamente reescrito
- Novo módulo: **Desdobramento** com algoritmo Greedy Covering Design
- Assistente IA: suporte a **Google Gemini** adicionado

### v4.0.0
- Reescrita completa do frontend (React + Tauri v2)
- Logic Pro com **20+ algoritmos** de análise matemática
- Análise X-Ray Pipeline

---

<div align="center">
  <a href="#-download">
    <img src="https://lotologic.com.br/social-image.png" width="600" alt="LotoLogic" />
  </a>
</div>

---

## 👨‍💻 Sobre o Autor

<div align="center">
  <img src="https://lotologic.com.br/sobre-autor.png" width="200" alt="Dante Testa" />
</div>

**Dante Testa** — Desenvolvedor, especialista em WordPress e IA, curioso de plantão.

Trabalho com desenvolvimento web e Inteligência Artificial — minha missão é usar tecnologia para resolver problemas reais e ensinar outras pessoas a fazerem o mesmo. O LotoLogic nasceu dessa curiosidade: será que dá pra aplicar análise de dados e IA num tema tão humano quanto a sorte? Aparentemente dá. 😄

Se o LotoLogic te ajudou, me siga nas redes — isso ajuda muito a manter o projeto vivo e crescendo! 🙏

<p align="center">
  <a href="https://www.youtube.com/channel/UCcYUV_knziHoPBFOwO1BbeA">
    <img src="https://img.shields.io/badge/YouTube-Inscreva--se-FF0000?style=for-the-badge&logo=youtube&logoColor=white" />
  </a>
  &nbsp;
  <a href="https://www.instagram.com/dantetesta_/">
    <img src="https://img.shields.io/badge/Instagram-Me%20siga-E4405F?style=for-the-badge&logo=instagram&logoColor=white" />
  </a>
  &nbsp;
  <a href="https://t.me/+OrYQ9YkFxN8xZDhh">
    <img src="https://img.shields.io/badge/Telegram-Grupo%20Oficial-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" />
  </a>
</p>

<p align="center">
  <a href="https://dantetesta.com.br">dantetesta.com.br</a>
</p>

---

<div align="center">
  <strong>LotoLogic v4.2.8</strong><br/>
  Feito com ❤️ para apostadores sérios
</div>
