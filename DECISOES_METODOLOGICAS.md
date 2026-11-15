# Decisões metodológicas

Registro das escolhas que definem a análise, com o motivo e o efeito de cada uma. Os números vêm de
[painel/preparar_dados.py](painel/preparar_dados.py) (saída em `painel/dados/funil_populacao.json`).

## D1. Unidade de análise: a escola (15/11/2026)

A análise é do **ENEM por escola**, não por aluno: cada observação é um estabelecimento de ensino.

- Desde a adequação à LGPD, o Censo Escolar publica os microdados por escola (contagens agregadas
  por `CO_ENTIDADE`), sem registros de alunos.
- As médias do ENEM são calculadas por escola a partir dos participantes que informaram a escola de
  conclusão do ensino médio.
- As conclusões valem para escolas, não para alunos. Uma escola com 10 participantes pesa o mesmo
  que uma com 300.

## D2. Bases e ligação (15/11/2026)

| Base | Versão | Arquivo usado | Fonte |
|---|---|---|---|
| Censo Escolar da Educação Básica 2025 | v2, julho de 2026 | Tabelas de escola, matrícula e docente | [INEP: microdados do Censo Escolar](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar) |
| ENEM 2025 | microdados 2025 | `RESULTADOS_2025.csv` (notas e escola) | [INEP: microdados do ENEM](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem) |

- **Chave:** `CO_ESCOLA` (ENEM) = `CO_ENTIDADE` (Censo). Nas escolas ligadas, a dependência
  administrativa informada pelas duas bases coincide em 100% dos casos.
- **Máscara do ENEM:** o código da escola é trocado por uma máscara quando ela tem menos de 10
  participantes (Leia-me do ENEM 2025). São 3.941 códigos, todos com no máximo 9 participantes, que
  não existem no Censo. Essas escolas ficam fora da análise por construção.

## D3. População (15/11/2026)

**Escolas em atividade, com ensino médio presencial e pelo menos 10 participantes do ENEM 2025
com as cinco notas.**

| Etapa | Critério | Escolas |
|---|---|---:|
| Cadastro do Censo 2025 | todas | 214.192 |
| Em atividade | `TP_SITUACAO_FUNCIONAMENTO = 1` | 180.540 |
| Com ensino médio | `QT_MAT_MED > 0` (matrículas no ensino médio regular) | 30.257 |
| Ensino médio presencial | `QT_MAT_MED − QT_MAT_MED_EAD > 0` (ao menos uma matrícula presencial no ensino médio) | 30.236 |
| **População** | **pelo menos 10 participantes do ENEM 2025 com as cinco notas** | **23.343** |

- **"Pelo menos 10 alunos"** é lido como pelo menos 10 participantes da escola com as cinco notas
  (ciências da natureza, ciências humanas, linguagens, matemática e redação), isto é, presentes nos
  dois dias. Isso dá ao menos 10 notas por média e coincide com o limite da máscara do ENEM.
- A população tem 5.203 municípios e 1.254.122 participantes com as cinco notas.

## D4. Notas da escola (15/11/2026)

- **Nota do participante:** a média simples das cinco notas, só para quem tem as cinco.
- **Nota da escola:** a média dessas notas entre os participantes da escola, que é a média geral.
  Também se calculam as médias de cada área (`ENEM_MEDIA_CN`, `_CH`, `_LC`, `_MT`, `_REDACAO`).
- Redações com nota zero (em branco, anuladas) entram como zero, que é a nota oficial do participante.
- A participação no ENEM é voluntária. Desde 2015 o INEP não calcula nem divulga o ENEM por Escola,
  e a média de uma escola reflete quem fez a prova, não todos os alunos. A taxa de participação
  (participantes ÷ matrículas da 3ª série, `TAXA_PARTICIPACAO_ENEM`) fica na base para
  qualificar essa limitação.

## D5. Cor/raça e perfil sociodemográfico: do Censo, não do questionário do ENEM (15/11/2026)

A intenção original era usar o questionário socioeconômico do ENEM. **Não é possível ligá-lo às
escolas:** o questionário está em `PARTICIPANTES_2025.csv`, que não tem o código da escola, e o
manual diz que "os arquivos PARTICIPANTES_2025.csv e RESULTADOS_2025.csv não possuem chave de
ligação em comum", de propósito, para proteger os participantes.

Por isso o perfil por cor/raça vem do **Censo Escolar**, que conta as matrículas de cada escola por
cor/raça:

- `PCT_BRANCA`, `PCT_PRETA`, `PCT_PARDA`, `PCT_AMARELA`, `PCT_INDIGENA` são percentuais **entre os
  alunos com cor/raça declarada**, e `PCT_PPI` soma pretos, pardos e indígenas.
- `PCT_COR_NAO_DECLARADA` acompanha a qualidade dessa informação: quanto maior, menos confiável o perfil.
- As contagens são da educação básica inteira da escola, não só do ensino médio, porque o Censo não
  separa cor/raça por etapa.
- Também ficam na base o percentual feminino das matrículas e o percentual de docentes com ensino
  superior.

## D6. Códigos especiais do Censo (15/11/2026)

- `88888` nas quantidades marca valor extremo e vira faltante, por exemplo em `QT_PROF_PSICOLOGO`.
- `9` em indicadores `IN_` significa "não informado" e vira faltante.

## D7. Mapa: território dos municípios (15/11/2026)

O Censo 2025 **retirou** endereço e coordenadas (`LATITUDE`, `LONGITUDE`) dos microdados. Pelo
dicionário, eles continuam públicos no [Catálogo de Escolas do INEP](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/inep-data/catalogo-de-escolas).

- O mapa mostra o **território de cada município**, colorido pelo número de escolas da população
  em faixas (nenhuma, 1, 2–3, 4–9, 10–49, 50 ou mais). A distribuição é muito assimétrica: metade
  dos municípios tem uma escola e São Paulo tem 1.096.
- A malha é a do IBGE (API de malhas v3), na qualidade mínima para municípios e intermediária para
  as UFs, com as coordenadas arredondadas para cerca de 100 m (`painel/preparar_dados.py`).
- Boa Esperança do Norte (MT), com 1 escola, não tem polígono na malha e fica fora só do mapa.
- O painel permite um recorte (drill-down) por região, UF e município. O mapa mostra a região ou a
  UF; os indicadores e as tabelas resumem o recorte escolhido.
- **Pendente (opcional):** exportar o Catálogo de Escolas para mostrar cada escola no seu ponto.

## D8. Tamanho e sorteio da amostra (15/11/2026)

**Amostra aleatória simples de 1.021 escolas, sem reposição.** Os parâmetros, o cálculo e o sorteio
estão em [painel/sortear_amostra.py](painel/sortear_amostra.py) e no Painel 2.

| Parâmetro | Valor | Por quê |
|---|---|---|
| Tamanho da população (N) | 23.343 | A população da D3 |
| Nível de confiança | 95% (z = 1,96) | Convenção usual; equilibra confiança e tamanho |
| Margem de erro (E) | 3 pontos percentuais | Separa diferenças de poucos pontos nas proporções com cerca de 4% da população |
| Proporção de planejamento (p) | 0,5 | Sem estimativa prévia; maximiza p(1 − p), então serve a qualquer proporção do trabalho |

- **Cálculo:** n₀ = z²·p(1−p)/E² = 1.067,07. Com a correção para população finita,
  n = n₀/(1 + (n₀−1)/N) = 1.020,47, arredondado para **1.021** (4,37% da população).
- **Médias:** uma só amostra serve a todas as hipóteses, por isso o n vem do cenário de proporção
  (o mais exigente com p = 0,5). Com n = 1.021 e o desvio-padrão da própria amostra, a margem de erro
  fica em ±3,7 pontos para a média geral do ENEM, ±4,5 em matemática e ±6,8 na redação.
- **Sorteio:** o cadastro são as 23.343 escolas em ordem crescente de `CO_ENTIDADE`.
  `numpy.random.default_rng(20261115).choice(N, size=1021, replace=False)` escolhe as posições, e
  cada escola tem probabilidade n/N = 4,37% de entrar.
- **Semente:** a data do sorteio. A lista sorteada fica gravada em `painel/dados/amostra.csv`. Rodar o
  script de novo com a mesma semente e o mesmo cadastro gera o mesmo arquivo, conferido pelo hash MD5.

## D9. Hipótese 1 (proporção): acesso dos alunos à internet, estratégia 7.15 do PNE (15/11/2026)

- **Âncora:** estratégia 7.15 do PNE 2014–2024 (Lei 13.005/2014): "universalizar, até o quinto ano de
  vigência deste PNE, o acesso à rede mundial de computadores em banda larga de alta velocidade [...]
  nas escolas da rede pública de educação básica". O prazo venceu em 2019. A Lei 14.180/2021 (Educação
  Conectada) foi criada em consonância com essa estratégia.
- **Domínio:** só as escolas **públicas** da população, porque a estratégia trata da rede pública.
  São N = 16.859 escolas, e 755 delas estão na amostra.
- **Parâmetro:** p é a proporção de escolas com internet para uso dos alunos (`IN_INTERNET_ALUNOS`).
- **Hipóteses:** H₀: p ≥ 0,90 (perto de universal) × H₁: p < 0,90, com α = 5% e teste z unilateral à
  esquerda. "Universal" (p = 1) não pode ser H₀, porque não tem variância; por isso "perto de universal"
  foi fixado em 90%.
- **Método:** teste z e intervalo de Wald de 95%, os dois com a correção para população finita
  (coerente com o cálculo do n). Código em `painel/inferencia.py` e `painel/hipoteses.py`.
- **Resultado:** p̂ = 85,03% (642 de 755), IC de 95% de 82,5% a 87,5%, z = −4,65, valor-p ≈ 1,6 × 10⁻⁶.
  **Rejeita H₀.** Na população, p = 85,05%: o IC contém p, e a decisão está correta (H₀ é falsa).
- **Variabilidade:** em 10.000 AAS simuladas (hipergeométrica exata), o teste rejeita H₀ em 99,5% das
  amostras (poder), e 94,8% dos intervalos contêm p.
- **Sensibilidade:** com p₀ = 0,85, a mesma amostra não rejeitaria H₀ (z ≈ 0,03).

## D10. Hipótese 2 (proporção): grêmio estudantil na maioria das escolas (15/11/2026)

- **Pergunta:** a maioria das escolas da população tem grêmio estudantil em funcionamento?
- **Âncoras:** a Lei 7.398/1985 assegura aos estudantes secundaristas a organização de grêmios. A
  estratégia 19.4 do PNE 2014–2024 manda "estimular, em todas as redes de educação básica, a
  constituição e o fortalecimento de grêmios estudantis [...]".
- **Domínio:** todas as escolas da população (N = 23.343; as 1.021 da amostra).
- **Parâmetro:** p é a proporção de escolas com grêmio estudantil (`IN_ORGAO_GREMIO_ESTUDANTIL`).
- **Hipóteses:** H₀: p ≤ 0,5 × H₁: p > 0,5, com α = 5% e teste z unilateral à direita. O p₀ = 0,5 sai
  da própria pergunta ("maioria" é mais da metade).
- **Resultado:** p̂ = 46,13% (471 de 1.021), IC de 95% de 43,1% a 49,1%, z = −2,53, valor-p = 0,994.
  **Não rejeita H₀**, e o IC inteiro fica abaixo de 50%: a amostra aponta na direção contrária à de H₁.
  Na população, p = 47,93%: H₀ é verdadeira, o IC contém p, e a decisão está correta.
- **Variabilidade:** em 10.000 AAS simuladas, o teste rejeitaria H₀ em 0,1% das amostras (menos que α,
  porque p está abaixo de 0,5), e 95,7% dos intervalos contêm p.
- **Ressalva:** as redes são muito diferentes. Na população, 62,0% das escolas públicas e 11,3% das
  privadas têm grêmio, e a conclusão se inverteria num teste só com as públicas.

## D11. Painel 3b, Hipótese 1 (médias): escolas privadas × públicas (15/11/2026)

- **Pergunta:** a média geral no ENEM das escolas privadas é maior que a das públicas?
- **Parâmetro:** μ_privadas − μ_públicas (`ENEM_MEDIA_GERAL`). Hipóteses H₀: μ_A − μ_B ≤ 0 × H₁: μ_A − μ_B > 0,
  com α = 5%, unilateral à direita.
- **Método:** teste t de Welch, que não supõe variâncias iguais (s²_A/s²_B = 1,40), com a correção para população
  finita em cada grupo: EP² = Σ (1 − n_g/N_g)·s²_g/n_g, e graus de liberdade de Welch–Satterthwaite. Os
  intervalos de cada média e da diferença usam a t de Student. Código em `painel/inferencia.py`.
- **Grupos:** 6.484 privadas e 16.859 públicas na população; 266 e 755 na amostra.
- **Resultado:** diferença de 106,7 pontos (600,5 × 493,8), IC de 95% de 100,9 a 112,5, t = 35,92 com 405,6 gl,
  valor-p ≈ 2 × 10⁻¹²⁸. **Rejeita H₀.** Na população, a diferença é 103,7 (600,0 × 496,3): o IC a contém, e a
  decisão está correta.
- **Variabilidade:** em 10.000 AAS de 1.021 escolas, o teste rejeita H₀ em 100% delas, 95,2% dos ICs contêm a
  diferença verdadeira, e a média das diferenças simuladas (103,66) coincide com a verdadeira.
- **Ressalvas:** a diferença não é causal (renda e seleção na entrada: 21,8% das privadas e 8,5% das públicas
  fazem exame de seleção); as federais (601, média de 580,7) estão na rede pública; a taxa de participação no
  ENEM difere entre as redes (mediana de 0,91 × 0,84).

## D12. Painel 3b, Hipótese 2 (médias): escolas de maioria negra × maioria branca (15/11/2026)

- **Pedido original:** comparar a nota média de **alunos** negros e brancos. **Não é possível com o ENEM 2025:**
  a cor/raça está em `PARTICIPANTES_2025.csv`, as notas em `RESULTADOS_2025.csv`, e os dois não têm chave de
  ligação em comum (ver D5). A unidade do trabalho também é a escola (D1).
- **Versão adotada (ecológica):** comparar a média geral no ENEM das **escolas** de maioria negra com a das de
  maioria branca, pela composição das matrículas no Censo. As conclusões valem para escolas, não para alunos
  (falácia ecológica), e isso está dito no painel.
- **Negros:** pretos e pardos, como no Estatuto da Igualdade Racial (Lei 12.288/2010, art. 1º, IV).
  `PCT_NEGRA` = `PCT_PRETA` + `PCT_PARDA`, entre as matrículas com cor/raça declarada.
- **Classificação (`COMPOSICAO_RACIAL`):** maioria negra se `PCT_NEGRA` > 50; maioria branca se `PCT_BRANCA`
  > 50. A escola só é classificada se ao menos 50% das matrículas tiverem cor/raça declarada
  (`LIMITE_NAO_DECLARADA` em `preparar_dados.py`). Na população, a composição fica assim:

  | Composição | Escolas |
  |---|---:|
  | Maioria negra | 11.671 |
  | Maioria branca | 10.198 |
  | Declaração insuficiente (fora; média de 561,1, 63% privadas) | 1.253 |
  | Sem maioria negra ou branca (fora) | 221 |
- **Hipóteses:** H₀: μ_negra − μ_branca ≥ 0 × H₁: μ_negra − μ_branca < 0, com α = 5%, unilateral à esquerda,
  teste de Welch (s²_A/s²_B = 0,61).
- **Resultado:** 518 e 448 escolas na amostra; diferença de −59,3 pontos (491,8 × 551,1), IC de 95% de −65,8 a
  −52,8, t = −17,80 com 839,6 gl, valor-p ≈ 1 × 10⁻⁶⁰. **Rejeita H₀.** Na população, a diferença é −59,2
  (495,7 × 555,0): o IC a contém, e a decisão está correta.
- **Variabilidade:** em 10.000 AAS, o teste rejeita H₀ em 100% delas, e 94,8% dos ICs contêm a diferença verdadeira.
- **Ressalva central:** parte da diferença vem da rede (42,6% das escolas de maioria branca são privadas, contra
  11,3% das de maioria negra), mas ela persiste dentro de cada rede: 606,9 × 576,1 nas privadas e 516,5 × 485,5
  nas públicas (população).

## Pendências

- Vídeo de apresentação (até 5 minutos) e publicação dos painéis com links abertos.
