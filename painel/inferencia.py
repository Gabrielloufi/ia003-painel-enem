"""Inferência para uma proporção: intervalo de confiança, teste z e simulação da variabilidade amostral.

A amostra é aleatória simples sem reposição de uma população finita conhecida, por isso os erros-padrão
levam a correção para população finita, sqrt((N - n)/(N - 1)), a mesma usada no tamanho da amostra.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist

import numpy as np
import pandas as pd

Z = NormalDist()
ALTERNATIVAS = {"menor": "<", "maior": ">", "diferente": "≠"}
NULAS = {"menor": "≥", "maior": "≤", "diferente": "="}


@dataclass(frozen=True)
class TesteProporcao:
    N: int  # tamanho da população (do domínio da hipótese)
    n: int  # escolas da amostra com a informação
    x: int  # escolas da amostra com o evento
    p0: float
    alternativa: str  # "menor", "maior" ou "diferente"
    alpha: float = 0.05
    confianca: float = 0.95

    @property
    def p_hat(self) -> float:
        return self.x / self.n

    @property
    def fpc(self) -> float:
        return math.sqrt((self.N - self.n) / (self.N - 1))

    @property
    def se0(self) -> float:
        """Erro-padrão sob H0 (usa p0): é o do teste."""
        return math.sqrt(self.p0 * (1 - self.p0) / self.n) * self.fpc

    @property
    def z(self) -> float:
        return (self.p_hat - self.p0) / self.se0

    @property
    def p_valor(self) -> float:
        if self.alternativa == "menor":
            return Z.cdf(self.z)
        if self.alternativa == "maior":
            return 1 - Z.cdf(self.z)
        return 2 * (1 - Z.cdf(abs(self.z)))

    @property
    def z_critico(self) -> float:
        if self.alternativa == "menor":
            return Z.inv_cdf(self.alpha)
        if self.alternativa == "maior":
            return Z.inv_cdf(1 - self.alpha)
        return Z.inv_cdf(1 - self.alpha / 2)  # região: |z| > z_critico

    @property
    def rejeita(self) -> bool:
        return self.p_valor < self.alpha

    @property
    def z_ic(self) -> float:
        return Z.inv_cdf(1 - (1 - self.confianca) / 2)

    @property
    def se(self) -> float:
        """Erro-padrão estimado (usa p̂): é o do intervalo de confiança."""
        return math.sqrt(self.p_hat * (1 - self.p_hat) / self.n) * self.fpc

    @property
    def ic(self) -> tuple[float, float]:
        return self.p_hat - self.z_ic * self.se, self.p_hat + self.z_ic * self.se

    def condicoes(self) -> list[tuple[str, float, bool]]:
        """Aproximação normal: ao menos 10 sucessos e 10 fracassos esperados (teste) e observados (intervalo)."""
        return [("n·p₀", self.n * self.p0, self.n * self.p0 >= 10),
                ("n·(1 − p₀)", self.n * (1 - self.p0), self.n * (1 - self.p0) >= 10),
                ("n·p̂", self.n * self.p_hat, self.n * self.p_hat >= 10),
                ("n·(1 − p̂)", self.n * (1 - self.p_hat), self.n * (1 - self.p_hat) >= 10)]


def teste_proporcao(amostra01: pd.Series, N: int, p0: float, alternativa: str, alpha: float = 0.05) -> TesteProporcao:
    """amostra01: o evento (1) ou não (0) nas escolas da amostra; faltantes ficam de fora."""
    s = amostra01.dropna()
    return TesteProporcao(N=N, n=len(s), x=int(s.sum()), p0=p0, alternativa=alternativa, alpha=alpha)


def simular_proporcao(K: int, N: int, n: int, p0: float, alternativa: str, alpha: float = 0.05,
                      repeticoes: int = 10_000, semente: int = 1) -> dict:
    """Repete o sorteio (AAS de n entre N, das quais K têm o evento) e aplica o mesmo teste e intervalo.

    Numa AAS sem reposição, o número de escolas com o evento segue exatamente a distribuição
    hipergeométrica, então cada repetição é um sorteio completo, sem aproximação.
    """
    x = np.random.default_rng(semente).hypergeometric(K, N - K, n, size=repeticoes)
    t = TesteProporcao(N=N, n=n, x=0, p0=p0, alternativa=alternativa, alpha=alpha)
    p_hat = x / n
    z = (p_hat - p0) / t.se0
    rejeita = z < t.z_critico if alternativa == "menor" else z > t.z_critico if alternativa == "maior" else np.abs(z) > t.z_critico
    se = np.sqrt(p_hat * (1 - p_hat) / n) * t.fpc
    p = K / N
    cobre = (p_hat - t.z_ic * se <= p) & (p <= p_hat + t.z_ic * se)
    return {"p_hat": p_hat, "taxa_rejeicao": float(rejeita.mean()), "cobertura": float(cobre.mean()),
            "repeticoes": repeticoes, "p_populacao": p}


# --- duas médias (grupos independentes da mesma AAS) ---------------------------------------------
from scipy import stats as _sps  # noqa: E402  (distribuição t de Student)


def classificar_decisao(rejeita: bool, h0_verdadeira: bool) -> str:
    if rejeita:
        return "um erro tipo I (rejeitou uma H₀ verdadeira)" if h0_verdadeira else "correta"
    return "correta" if h0_verdadeira else "um erro tipo II (não rejeitou uma H₀ falsa)"


@dataclass(frozen=True)
class Grupo:
    n: int
    media: float
    dp: float
    N: int  # tamanho do grupo na população

    @property
    def var_media(self) -> float:
        """Variância estimada da média amostral numa AAS sem reposição: (1 − n/N) s²/n."""
        return (1 - self.n / self.N) * self.dp**2 / self.n

    def ic(self, confianca: float = 0.95) -> tuple[float, float]:
        t = _sps.t.ppf(1 - (1 - confianca) / 2, self.n - 1)
        return self.media - t * math.sqrt(self.var_media), self.media + t * math.sqrt(self.var_media)


@dataclass(frozen=True)
class TesteDuasMedias:
    """Teste t de Welch para μ_A − μ_B, com a correção para população finita em cada grupo."""
    a: Grupo
    b: Grupo
    alternativa: str  # sobre μ_A − μ_B: "menor", "maior" ou "diferente"
    delta0: float = 0.0
    alpha: float = 0.05
    confianca: float = 0.95

    @property
    def diferenca(self) -> float:
        return self.a.media - self.b.media

    @property
    def se(self) -> float:
        return math.sqrt(self.a.var_media + self.b.var_media)

    @property
    def gl(self) -> float:
        """Graus de liberdade de Welch–Satterthwaite."""
        va, vb = self.a.var_media, self.b.var_media
        return (va + vb) ** 2 / (va**2 / (self.a.n - 1) + vb**2 / (self.b.n - 1))

    @property
    def t(self) -> float:
        return (self.diferenca - self.delta0) / self.se

    @property
    def p_valor(self) -> float:
        if self.alternativa == "menor":
            return float(_sps.t.cdf(self.t, self.gl))
        if self.alternativa == "maior":
            return float(_sps.t.sf(self.t, self.gl))
        return float(2 * _sps.t.sf(abs(self.t), self.gl))

    @property
    def t_critico(self) -> float:
        if self.alternativa == "menor":
            return float(_sps.t.ppf(self.alpha, self.gl))
        if self.alternativa == "maior":
            return float(_sps.t.ppf(1 - self.alpha, self.gl))
        return float(_sps.t.ppf(1 - self.alpha / 2, self.gl))

    @property
    def rejeita(self) -> bool:
        return self.p_valor < self.alpha

    @property
    def t_ic(self) -> float:
        return float(_sps.t.ppf(1 - (1 - self.confianca) / 2, self.gl))

    @property
    def ic(self) -> tuple[float, float]:
        return self.diferenca - self.t_ic * self.se, self.diferenca + self.t_ic * self.se


def grupo(valores: pd.Series, N: int) -> Grupo:
    v = valores.dropna()
    return Grupo(n=len(v), media=float(v.mean()), dp=float(v.std()), N=N)


def simular_duas_medias(valores: np.ndarray, rotulos: np.ndarray, n: int, alternativa: str, alpha: float = 0.05,
                        repeticoes: int = 10_000, semente: int = 1, confianca: float = 0.95) -> dict:
    """Repete a AAS de n escolas da população inteira e refaz o teste com os grupos que caírem em cada amostra.

    valores: a variável na população; rotulos: "A", "B" ou "" (fora dos dois grupos), na mesma ordem.
    Vetorizado: as repetições são as linhas de uma matriz; as contas são as mesmas de TesteDuasMedias.
    """
    rng = np.random.default_rng(semente)
    N = len(valores)
    em_a, em_b = rotulos == "A", rotulos == "B"
    Na, Nb = int(em_a.sum()), int(em_b.sum())
    verdade = float(valores[em_a].mean() - valores[em_b].mean())
    idx = np.stack([rng.choice(N, size=n, replace=False) for _ in range(repeticoes)])
    V, A, B = valores[idx], em_a[idx], em_b[idx]

    def estatisticas(M: np.ndarray, Ng: int):
        ng = M.sum(axis=1)
        media = (V * M).sum(axis=1) / ng
        s2 = (((V - media[:, None]) ** 2) * M).sum(axis=1) / (ng - 1)
        return ng, media, (1 - ng / Ng) * s2 / ng

    na, ma, va = estatisticas(A, Na)
    nb, mb, vb = estatisticas(B, Nb)
    dif, se = ma - mb, np.sqrt(va + vb)
    gl = (va + vb) ** 2 / (va**2 / (na - 1) + vb**2 / (nb - 1))
    t = dif / se
    if alternativa == "menor":
        rejeita = t < _sps.t.ppf(alpha, gl)
    elif alternativa == "maior":
        rejeita = t > _sps.t.ppf(1 - alpha, gl)
    else:
        rejeita = np.abs(t) > _sps.t.ppf(1 - alpha / 2, gl)
    margem = _sps.t.ppf(1 - (1 - confianca) / 2, gl) * se
    cobre = (dif - margem <= verdade) & (verdade <= dif + margem)
    return {"diferencas": dif, "taxa_rejeicao": float(rejeita.mean()), "cobertura": float(cobre.mean()),
            "repeticoes": repeticoes, "diferenca_populacao": verdade}
