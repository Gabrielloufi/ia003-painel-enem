"""As variáveis de análise da base do painel: rótulo, tipo, fonte e descrição.

Uma linha por variável que entra nos painéis. As colunas auxiliares da base (contagens usadas só
para calcular percentuais, coordenadas) ficam de fora.
"""

QUALI_NOMINAL = "Qualitativa nominal"
QUALI_BINARIA = "Qualitativa binária (sim/não)"
QUANTI_DISCRETA = "Quantitativa discreta"
QUANTI_CONTINUA = "Quantitativa contínua"

CENSO = "Censo Escolar 2025"
ENEM = "ENEM 2025"
CENSO_CALC = "Censo Escolar 2025 (calculada)"
ENEM_CENSO_CALC = "ENEM 2025 e Censo (calculada)"

VARIAVEIS = {
    # --- qualitativas: caracterização da escola ---
    "REDE": ("Rede", QUALI_NOMINAL, CENSO, "Pública ou privada (CO_REDE)."),
    "DEPENDENCIA": ("Dependência administrativa", QUALI_NOMINAL, CENSO, "Federal, estadual, municipal ou privada (TP_DEPENDENCIA)."),
    "LOCALIZACAO": ("Localização", QUALI_NOMINAL, CENSO, "Urbana ou rural (TP_LOCALIZACAO)."),
    "NO_REGIAO": ("Região", QUALI_NOMINAL, CENSO, "Região geográfica da escola."),
    "SG_UF": ("UF", QUALI_NOMINAL, CENSO, "Unidade da Federação da escola."),
    "COMPOSICAO_RACIAL": ("Composição racial das matrículas", QUALI_NOMINAL, CENSO_CALC,
                          "Maioria negra (pretos e pardos > 50%) ou branca (> 50%) entre as matrículas com cor/raça "
                          "declarada; só se ao menos metade das matrículas tem cor/raça declarada."),
    # --- qualitativas: infraestrutura e serviços (eventos para proporções) ---
    "IN_INTERNET_ALUNOS": ("Internet para os alunos", QUALI_BINARIA, CENSO, "A escola tem acesso à internet para uso dos alunos."),
    "IN_BIBLIOTECA_SALA_LEITURA": ("Biblioteca ou sala de leitura", QUALI_BINARIA, CENSO, "Existe e é utilizada biblioteca ou sala de leitura."),
    "IN_LABORATORIO_CIENCIAS": ("Laboratório de ciências", QUALI_BINARIA, CENSO, "Existe e é utilizado laboratório de ciências."),
    "IN_LABORATORIO_INFORMATICA": ("Laboratório de informática", QUALI_BINARIA, CENSO, "Existe e é utilizado laboratório de informática."),
    "IN_QUADRA_ESPORTES": ("Quadra de esportes", QUALI_BINARIA, CENSO, "Existe e é utilizada quadra de esportes (coberta ou descoberta)."),
    "IN_ESGOTO_REDE_PUBLICA": ("Esgoto da rede pública", QUALI_BINARIA, CENSO, "O esgoto sanitário vai para a rede pública."),
    "IN_BANHEIRO_PNE": ("Banheiro acessível", QUALI_BINARIA, CENSO, "Banheiro adequado a pessoas com deficiência ou mobilidade reduzida."),
    "IN_ACESSIBILIDADE_INEXISTENTE": ("Nenhum recurso de acessibilidade", QUALI_BINARIA, CENSO, "A escola não tem nenhum dos recursos de acessibilidade listados."),
    "IN_ORGAO_GREMIO_ESTUDANTIL": ("Grêmio estudantil", QUALI_BINARIA, CENSO, "Há grêmio estudantil em funcionamento."),
    "IN_EXAME_SELECAO": ("Exame de seleção", QUALI_BINARIA, CENSO, "A escola faz exame de seleção para ingresso dos alunos."),
    "TEM_PSICOLOGO": ("Psicólogo(a) na escola", QUALI_BINARIA, CENSO_CALC, "Pelo menos um psicólogo escolar (QT_PROF_PSICOLOGO > 0)."),
    # --- quantitativas: desempenho no ENEM ---
    "ENEM_MEDIA_GERAL": ("Média geral no ENEM", QUANTI_CONTINUA, ENEM, "Média, entre os participantes da escola, da média simples das cinco notas."),
    "ENEM_MEDIA_CN": ("Média em ciências da natureza", QUANTI_CONTINUA, ENEM, "Média da nota de ciências da natureza dos participantes."),
    "ENEM_MEDIA_CH": ("Média em ciências humanas", QUANTI_CONTINUA, ENEM, "Média da nota de ciências humanas dos participantes."),
    "ENEM_MEDIA_LC": ("Média em linguagens", QUANTI_CONTINUA, ENEM, "Média da nota de linguagens e códigos dos participantes."),
    "ENEM_MEDIA_MT": ("Média em matemática", QUANTI_CONTINUA, ENEM, "Média da nota de matemática dos participantes."),
    "ENEM_MEDIA_REDACAO": ("Média na redação", QUANTI_CONTINUA, ENEM, "Média da nota da redação dos participantes."),
    "ENEM_COM_NOTAS": ("Participantes com as cinco notas", QUANTI_DISCRETA, ENEM, "Participantes da escola presentes nos dois dias, com as cinco notas."),
    "TAXA_PARTICIPACAO_ENEM": ("Taxa de participação no ENEM", QUANTI_CONTINUA, ENEM_CENSO_CALC, "Participantes do ENEM ÷ matrículas na 3ª série do ensino médio."),
    # --- quantitativas: porte e perfil ---
    "QT_MAT_MED": ("Matrículas no ensino médio", QUANTI_DISCRETA, CENSO, "Matrículas no ensino médio regular."),
    "QT_DOC_BAS": ("Docentes", QUANTI_DISCRETA, CENSO, "Docentes da educação básica na escola."),
    "QT_SALAS_UTILIZADAS": ("Salas de aula utilizadas", QUANTI_DISCRETA, CENSO, "Salas de aula utilizadas, dentro e fora do prédio."),
    "PCT_PPI": ("% de pretos, pardos e indígenas", QUANTI_CONTINUA, CENSO_CALC, "Entre as matrículas com cor/raça declarada."),
    "PCT_NEGRA": ("% de negros (pretos e pardos)", QUANTI_CONTINUA, CENSO_CALC, "Entre as matrículas com cor/raça declarada."),
    "PCT_BRANCA": ("% de brancos", QUANTI_CONTINUA, CENSO_CALC, "Entre as matrículas com cor/raça declarada."),
    "PCT_COR_NAO_DECLARADA": ("% sem cor/raça declarada", QUANTI_CONTINUA, CENSO_CALC, "Matrículas sem cor/raça declarada ÷ total de matrículas."),
    "PCT_FEMININO": ("% de matrículas femininas", QUANTI_CONTINUA, CENSO_CALC, "Matrículas do sexo feminino ÷ total de matrículas."),
    "PCT_DOC_SUPERIOR": ("% de docentes com ensino superior", QUANTI_CONTINUA, CENSO_CALC, "Docentes com graduação ÷ total de docentes."),
}


def rotulo(coluna: str) -> str:
    return VARIAVEIS.get(coluna, (coluna,))[0]
