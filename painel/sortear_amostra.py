"""Dimensiona e sorteia a amostra aleatória simples (AAS), sem reposição, da população do painel.

Parâmetros e justificativa em DECISOES_METODOLOGICAS.md (D8). Roda uma vez: a lista sorteada fica
gravada e o painel só a lê, então a amostra não muda entre execuções do painel.

Entrada: dados/escolas_populacao.parquet (gerado por preparar_dados.py).
Saída:   dados/amostra.csv (escolas sorteadas, na ordem do sorteio) e dados/amostra.json (parâmetros).

    python sortear_amostra.py
"""
from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

DADOS = Path(__file__).resolve().parent / "dados"

CONFIANCA = 0.95  # nível de confiança
MARGEM = 0.03  # margem de erro para proporções (3 pontos percentuais)
P_PLANEJAMENTO = 0.5  # proporção usada no dimensionamento (pior caso: maximiza p(1 - p))
SEMENTE = 20261115  # data do sorteio; fixa o gerador para reproduzir a mesma amostra


def main() -> None:
    # Cadastro: as escolas da população em ordem crescente de código do INEP
    cadastro = (pd.read_parquet(DADOS / "escolas_populacao.parquet", columns=["CO_ENTIDADE"])
                .sort_values("CO_ENTIDADE").reset_index(drop=True))
    N = len(cadastro)

    z = NormalDist().inv_cdf(1 - (1 - CONFIANCA) / 2)
    n0 = z**2 * P_PLANEJAMENTO * (1 - P_PLANEJAMENTO) / MARGEM**2
    n_corrigido = n0 / (1 + (n0 - 1) / N)  # correção para população finita
    n = math.ceil(n_corrigido)

    # AAS sem reposição: n posições distintas do cadastro, todas com a mesma chance de sair
    gerador = np.random.default_rng(SEMENTE)
    posicoes = gerador.choice(N, size=n, replace=False)
    amostra = pd.DataFrame({
        "ORDEM_SORTEIO": np.arange(1, n + 1),
        "POSICAO_CADASTRO": posicoes + 1,
        "CO_ENTIDADE": cadastro.loc[posicoes, "CO_ENTIDADE"].to_numpy(),
    })
    assert amostra["CO_ENTIDADE"].is_unique
    amostra.to_csv(DADOS / "amostra.csv", index=False)

    parametros = {
        "N": N, "confianca": CONFIANCA, "z": z, "margem": MARGEM, "p_planejamento": P_PLANEJAMENTO,
        "n0": n0, "n_corrigido": n_corrigido, "n": n, "fracao_amostral": n / N,
        "semente": SEMENTE, "gerador": f"numpy.random.default_rng (PCG64), numpy {np.__version__}",
        "metodo": "amostra aleatória simples sem reposição: Generator.choice(N, size=n, replace=False) "
                  "sobre o cadastro ordenado por CO_ENTIDADE",
        "data_sorteio": date.today().isoformat(),
    }
    (DADOS / "amostra.json").write_text(json.dumps(parametros, indent=1, ensure_ascii=False))
    print(json.dumps(parametros, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
