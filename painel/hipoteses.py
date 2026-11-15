"""As hipóteses do Painel 3. Cada uma é uma especificação; a página desenha todas do mesmo jeito.

Para acrescentar uma hipótese de proporção, basta uma nova HipoteseProporcao na lista PROPORCOES.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import pandas as pd

DOMINIOS: dict[str, tuple[str, Callable[[pd.DataFrame], pd.DataFrame]]] = {
    "todas": ("escolas da população", lambda d: d),
    "publicas": ("escolas públicas da população", lambda d: d[d["REDE"] == "Pública"]),
}


@dataclass(frozen=True)
class HipoteseProporcao:
    codigo: str
    titulo: str
    variavel: str  # coluna 0/1 da base
    evento: str  # o que conta como "sucesso"
    dominio: str  # chave de DOMINIOS
    p0: float
    alternativa: str  # "menor", "maior" ou "diferente"
    h0: str  # leitura de H0 em palavras
    h1: str
    contexto: str  # markdown
    porque_p0: str  # markdown
    limitacoes: list[str] = field(default_factory=list)
    alpha: float = 0.05


PROPORCOES = [
    HipoteseProporcao(
        codigo="1",
        titulo="Acesso dos alunos à internet nas escolas públicas",
        variavel="IN_INTERNET_ALUNOS",
        evento="a escola tem acesso à internet para uso dos alunos (Censo Escolar 2025)",
        dominio="publicas",
        p0=0.90,
        alternativa="menor",
        h0="o acesso dos alunos à internet está perto de universal nas escolas públicas",
        h1="o acesso ainda não está perto de universal",
        contexto=(
            "O Plano Nacional de Educação 2014–2024 ([Lei 13.005/2014](https://planalto.gov.br/ccivil_03/_ato2011-2014/2014/lei/l13005.htm)), "
            "na **estratégia 7.15**, determina:\n\n"
            "> universalizar, até o quinto ano de vigência deste PNE, o acesso à rede mundial de computadores em "
            "banda larga de alta velocidade e triplicar, até o final da década, a relação computador/aluno(a) nas "
            "escolas da rede pública de educação básica, promovendo a utilização pedagógica das tecnologias da "
            "informação e da comunicação;\n\n"
            "O prazo de universalização venceu em 2019. A Política de Inovação Educação Conectada "
            "([Lei 14.180/2021](https://planalto.gov.br/ccivil_03/_Ato2019-2022/2021/Lei/L14180.htm)) foi criada "
            "em consonância com essa estratégia, para apoiar a universalização do acesso à internet. A pergunta é "
            "se, em 2025, o acesso **dos alunos** à internet nas escolas públicas de ensino médio da população já "
            "está perto de universal."
        ),
        porque_p0=(
            "\"Universal\" seria p = 1, que não pode ser a hipótese nula: sem variância, qualquer escola sem "
            "internet a derrubaria. **\"Perto de universal\" é tomado como pelo menos 90% das escolas.** O teste é "
            "unilateral à esquerda: só a evidência de que a proporção está **abaixo** desse patamar interessa à "
            "pergunta."
        ),
        limitacoes=[
            "O Censo registra se há internet para uso dos alunos, não a velocidade: a estratégia fala em banda "
            "larga de **alta velocidade**, que esta variável não mede.",
            "A informação é declarada pela escola ao Censo Escolar.",
            "O patamar de 90% é uma escolha deste trabalho e a conclusão depende dele: com p₀ = 85%, a mesma "
            "amostra não rejeitaria H₀ (z ≈ 0,03; valor-p ≈ 0,51).",
            "A unidade é a escola: ter internet para os alunos não quer dizer que todos os alunos a usem.",
            "Só entram as escolas públicas da população (ensino médio presencial, ao menos 10 participantes do "
            "ENEM): o resultado não vale para todas as escolas públicas do país.",
        ],
    ),
    HipoteseProporcao(
        codigo="2",
        titulo="Grêmio estudantil na maioria das escolas",
        variavel="IN_ORGAO_GREMIO_ESTUDANTIL",
        evento="há grêmio estudantil em funcionamento na escola (Censo Escolar 2025)",
        dominio="todas",
        p0=0.50,
        alternativa="maior",
        h0="no máximo metade das escolas tem grêmio estudantil",
        h1="a maioria das escolas tem grêmio estudantil",
        contexto=(
            "O grêmio é a entidade que representa os estudantes dentro da escola. A "
            "[Lei 7.398/1985](https://planalto.gov.br/ccivil_03/leis/L7398.htm) assegura aos estudantes "
            "secundaristas a organização de grêmios estudantis como entidades autônomas, e o Plano Nacional de "
            "Educação 2014–2024 ([Lei 13.005/2014](https://planalto.gov.br/ccivil_03/_ato2011-2014/2014/lei/l13005.htm)), "
            "na **estratégia 19.4**, determina:\n\n"
            "> estimular, em todas as redes de educação básica, a constituição e o fortalecimento de grêmios "
            "estudantis e associações de pais, assegurando-se-lhes, inclusive, espaços adequados e condições de "
            "funcionamento nas escolas e fomentando a sua articulação orgânica com os conselhos escolares, por meio "
            "das respectivas representações;\n\n"
            "A pergunta é se, em 2025, **a maioria** das escolas de ensino médio da população tem grêmio estudantil "
            "em funcionamento."
        ),
        porque_p0=(
            "\"Maioria\" é mais da metade: **p₀ = 0,5** sai da própria pergunta, sem patamar arbitrário. O teste é "
            "unilateral à direita, porque só a evidência de que a proporção está **acima** de 50% sustenta que a "
            "maioria tem grêmio. Sem essa evidência, fica-se com H₀ (no máximo metade)."
        ),
        limitacoes=[
            "O Censo registra se há grêmio em funcionamento, declarado pela escola; não mede se ele é ativo, "
            "eleito ou representativo.",
            "Entram escolas públicas e privadas, e as duas redes são muito diferentes: na população, 62,0% das "
            "públicas e 11,3% das privadas têm grêmio. Só nas públicas a maioria tem; a proporção do conjunto "
            "mistura as duas realidades.",
            "\"Não rejeitar H₀\" não prova que no máximo metade das escolas tenha grêmio: só diz que a amostra "
            "não trouxe evidência de que a maioria tenha.",
            "A unidade é a escola: o resultado não diz quantos alunos estudam em escolas com grêmio.",
            "Só entram as escolas da população (ensino médio presencial, ao menos 10 participantes do ENEM).",
        ],
    ),
]


# --- médias: comparação de dois grupos de escolas (Painel 3b) ------------------------------------
GRUPOS: dict[str, tuple[str, Callable[[pd.DataFrame], pd.Series]]] = {
    "privada": ("Escolas privadas", lambda d: d["REDE"] == "Privada"),
    "publica": ("Escolas públicas", lambda d: d["REDE"] == "Pública"),
    "maioria_negra": ("Escolas de maioria negra", lambda d: d["COMPOSICAO_RACIAL"] == "Maioria negra"),
    "maioria_branca": ("Escolas de maioria branca", lambda d: d["COMPOSICAO_RACIAL"] == "Maioria branca"),
}


@dataclass(frozen=True)
class HipoteseMedias:
    codigo: str
    titulo: str
    variavel: str  # quantitativa da base
    grupo_a: str  # chaves de GRUPOS; o parâmetro é μ_A − μ_B
    grupo_b: str
    alternativa: str  # sobre μ_A − μ_B: "menor", "maior" ou "diferente"
    h0: str
    h1: str
    contexto: str
    porque: str
    limitacoes: list[str] = field(default_factory=list)
    delta0: float = 0.0
    alpha: float = 0.05


MEDIAS = [
    HipoteseMedias(
        codigo="1",
        titulo="Escolas privadas têm média maior no ENEM que as públicas?",
        variavel="ENEM_MEDIA_GERAL",
        grupo_a="privada",
        grupo_b="publica",
        alternativa="maior",
        h0="a média das escolas privadas não é maior que a das públicas",
        h1="a média das escolas privadas é maior que a das públicas",
        contexto=(
            "A rede (pública ou privada) é um dos recortes mais usados para discutir desigualdade educacional. "
            "Na população, 72% das escolas são públicas (federais, estaduais e municipais) e 28% privadas. "
            "A pergunta é se, entre as escolas de ensino médio da população, a **média geral no ENEM** das escolas "
            "privadas é maior que a das públicas."
        ),
        porque=(
            "O parâmetro é a diferença **μ_privadas − μ_públicas** entre as médias populacionais das duas redes, e "
            "δ₀ = 0, porque a pergunta é só qual rede tem média maior. O teste é unilateral à direita. Usa-se o "
            "teste t de Welch, que não supõe variâncias iguais, porque os desvios-padrão das duas redes diferem."
        ),
        limitacoes=[
            "A diferença não é causal: as redes atendem públicos diferentes (renda das famílias, seleção na "
            "entrada), que o Censo não mede. Na população, 21,8% das privadas e 8,5% das públicas fazem exame de "
            "seleção.",
            "A rede pública junta realidades distintas: as 601 escolas federais têm média de 580,7 na população, "
            "bem acima das estaduais.",
            "A participação no ENEM é voluntária e difere entre as redes: a taxa de participação mediana é 0,91 nas "
            "privadas e 0,84 nas públicas.",
            "A unidade é a escola: cada escola pesa o mesmo, tenha 10 ou 300 participantes.",
        ],
    ),
    HipoteseMedias(
        codigo="2",
        titulo="Escolas de maioria negra têm média menor no ENEM que as de maioria branca?",
        variavel="ENEM_MEDIA_GERAL",
        grupo_a="maioria_negra",
        grupo_b="maioria_branca",
        alternativa="menor",
        h0="a média das escolas de maioria negra não é menor que a das de maioria branca",
        h1="a média das escolas de maioria negra é menor que a das de maioria branca",
        contexto=(
            "A pergunta original era se **alunos negros** têm nota média menor que **alunos brancos**. Com os "
            "microdados do ENEM 2025 isso não é possível: a cor/raça está no arquivo de participantes e as notas no "
            "de resultados, e o manual avisa que \"os arquivos PARTICIPANTES_2025.csv e RESULTADOS_2025.csv não "
            "possuem chave de ligação em comum\".\n\n"
            "A versão possível é **no nível da escola**: compara-se a média geral no ENEM das escolas de maioria "
            "negra com a das escolas de maioria branca, pela composição das matrículas no Censo Escolar. Negros são "
            "pretos e pardos, como no Estatuto da Igualdade Racial "
            "([Lei 12.288/2010](https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2010/lei/l12288.htm), art. 1º, "
            "IV): \"o conjunto de pessoas que se autodeclaram pretas e pardas, conforme o quesito cor ou raça usado "
            "pela\" Fundação IBGE.\n\n"
            "**Maioria negra:** pretos e pardos são mais de 50% das matrículas com cor/raça declarada. **Maioria "
            "branca:** brancos são mais de 50%. Só se classifica a escola se ao menos metade das matrículas tem "
            "cor/raça declarada."
        ),
        porque=(
            "O parâmetro é **μ_maioria negra − μ_maioria branca**, com δ₀ = 0. O teste é unilateral à esquerda, "
            "porque a pergunta é se as escolas de maioria negra têm média **menor**. Usa-se o teste t de Welch."
        ),
        limitacoes=[
            "É uma comparação entre escolas, não entre alunos (falácia ecológica): escolas de maioria negra têm "
            "alunos brancos e vice-versa, e o resultado não mede a diferença entre alunos negros e brancos.",
            "Parte da diferença vem da rede: na população, 42,6% das escolas de maioria branca são privadas, "
            "contra 11,3% das de maioria negra. Mesmo dentro de cada rede, porém, a diferença persiste: 606,9 contra "
            "576,1 nas privadas e 516,5 contra 485,5 nas públicas.",
            "A cor/raça é a das matrículas de toda a educação básica da escola, não só do ensino médio.",
            "Ficam de fora 1.253 escolas com cor/raça declarada em menos da metade das matrículas (média de 561,1, "
            "63% privadas) e 221 sem maioria negra nem branca.",
            "A diferença não é causal: renda, rede, região e outros fatores andam junto com a composição racial.",
        ],
    ),
]
