# ENEM 2025 por escola, com o Censo Escolar 2025

Painéis interativos em Streamlit para o trabalho de **IA003, Estatística para Inteligência Artificial**
(UFRGS). O trabalho aplica amostragem, intervalos de confiança e testes de hipóteses a uma base grande e
compara os resultados da amostra com os da população inteira.

A base liga o desempenho das escolas de ensino médio no **ENEM 2025** às características delas no **Censo
Escolar 2025**, ambos do INEP. A unidade de análise é a **escola**.

## Os painéis

**App publicado:** <https://ufrgs-iaa003-painel-enem.streamlit.app/>

| Painel | Link | Conteúdo |
|---|---|---|
| 0. Base de dados | [/base-de-dados](https://ufrgs-iaa003-painel-enem.streamlit.app/base-de-dados) | Fonte, contexto, observações e variáveis, população e unidade amostral |
| 1. População | [/populacao](https://ufrgs-iaa003-painel-enem.streamlit.app/populacao) | Mapa por município, recorte por região, UF e município, resumo e distribuição de cada variável |
| 2. Amostra | [/amostra](https://ufrgs-iaa003-painel-enem.streamlit.app/amostra) | Tamanho da amostra (cálculo passo a passo), sorteio da amostra aleatória simples, a mesma análise do Painel 1 com a população como referência |
| 3a. Proporções | [/inferencia-proporcoes](https://ufrgs-iaa003-painel-enem.streamlit.app/inferencia-proporcoes) | Duas hipóteses de proporção: intervalo de confiança, teste z, comparação com a população e simulação da variabilidade amostral |
| 3b. Médias | [/inferencia-medias](https://ufrgs-iaa003-painel-enem.streamlit.app/inferencia-medias) | Duas hipóteses de diferença de médias: teste t de Welch, intervalos, comparação com a população e simulação |

## População, amostra e hipóteses

- **População:** as **23.343 escolas** em atividade, com ensino médio presencial e pelo menos 10
  participantes do ENEM 2025 com as cinco notas.
- **Ligação entre as bases:** o código da escola no ENEM (`CO_ESCOLA`) é o código no Censo (`CO_ENTIDADE`).
- **Amostra:** aleatória simples, sem reposição, de **1.021 escolas**, com 95% de confiança, margem de 3
  pontos percentuais e p = 0,5, mais a correção para população finita. A semente é fixa (20261115).

| Painel | Hipótese | Amostra | População |
|---|---|---|---|
| 3a | **1.** O acesso dos alunos à internet nas escolas públicas está perto de universal (estratégia 7.15 do PNE)? H₀: p ≥ 0,90 | p̂ = 85,0%, IC de 95% de 82,5% a 87,5%: **rejeita H₀** | p = 85,05% |
| 3a | **2.** A maioria das escolas tem grêmio estudantil? H₀: p ≤ 0,50 | p̂ = 46,1%, IC de 43,1% a 49,1%: **não rejeita H₀** | p = 47,93% |
| 3b | **1.** Escolas privadas têm média maior no ENEM que as públicas? H₀: μ_priv − μ_púb ≤ 0 | +106,7 pontos, IC de 100,9 a 112,5: **rejeita H₀** | +103,7 |
| 3b | **2.** Escolas de maioria negra têm média menor que as de maioria branca? H₀: μ_negra − μ_branca ≥ 0 | −59,3 pontos, IC de −65,8 a −52,8: **rejeita H₀** | −59,2 |

Nas quatro hipóteses, o intervalo contém o valor verdadeiro da população e a decisão do teste está correta.
A hipótese 2 do Painel 3b compara **escolas**, não alunos. O ENEM 2025 não permite ligar a cor/raça do
participante à nota, então a composição racial vem das matrículas da escola no Censo.

Cada escolha (população, códigos especiais, composição racial, tamanho da amostra, hipóteses) está
justificada em [DECISOES_METODOLOGICAS.md](DECISOES_METODOLOGICAS.md).

## Como rodar

Requer Python 3.10 ou superior.

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r painel/requirements.txt
streamlit run painel/app.py
```

Os dados processados (cerca de 7 MB) já estão em `painel/dados/`, então o painel roda sem baixar nada.

## Como regenerar os dados

Os microdados brutos (cerca de 3 GB) não estão no repositório. Para reconstruir a base do painel:

1. Baixe do INEP os microdados do [Censo Escolar 2025](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar)
   e do [ENEM 2025](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem).
2. Extraia os dois na pasta `dados/` da raiz, criando `dados/microdados_censo_escolar_2025_v2/` e
   `dados/microdados_enem_2025/`. O `RESULTADOS_2025.csv` vem compactado em Deflate64: use o 7-Zip ou o
   pacote `zipfile-deflate64`.
3. Rode `python painel/preparar_dados.py`. Na primeira vez ele também baixa as malhas de UFs e municípios da
   API do IBGE.
4. Rode `python painel/sortear_amostra.py` para refazer o sorteio. Com a mesma semente e o mesmo cadastro, a
   amostra sai idêntica.

## Estrutura

```
painel/
├── app.py                  navegação entre os painéis
├── paginas/                um arquivo por painel
├── componentes.py          recorte, indicadores, mapa, tabelas e gráficos dos painéis 1 e 2
├── descritiva.py           frequências e medidas descritivas
├── inferencia.py           intervalos, teste z, teste t de Welch e simulações
├── hipoteses.py            as quatro hipóteses (contexto, H₀, H₁, limitações)
├── variaveis.py            dicionário das variáveis de análise
├── dados_painel.py         leitura dos dados e formatação
├── preparar_dados.py       microdados → base do painel
├── sortear_amostra.py      tamanho e sorteio da amostra
└── dados/                  base processada, amostra sorteada, malhas do IBGE
DECISOES_METODOLOGICAS.md   as decisões do trabalho, com motivos e números
```

## Fontes

- INEP: [Microdados do Censo Escolar da Educação Básica 2025](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar) e
  [Microdados do ENEM 2025](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem).
- IBGE: [API de malhas geográficas](https://servicodados.ibge.gov.br/api/docs/malhas?versao=3) (UFs e municípios).
