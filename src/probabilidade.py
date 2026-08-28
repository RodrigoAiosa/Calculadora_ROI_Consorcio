"""
Simulador de probabilidade de contemplação por sorteio.

Modelo simplificado: em cada assembleia mensal, 1 cota é sorteada entre as
cotas ainda não contempladas (excluindo quem já foi contemplado por lance ou
sorteio em meses anteriores). A probabilidade de UM participante específico
ser sorteado em um mês qualquer é `1 / cotas_remanescentes` naquele mês.

Este é um modelo educacional — grupos reais podem sortear mais de uma cota
por mês, e a dinâmica de entrada/saída de participantes é mais complexa.
"""

from dataclasses import dataclass


@dataclass
class ResultadoProbabilidade:
    meses: list[int]
    prob_mensal: list[float]
    prob_acumulada: list[float]
    mes_50_perc: int | None
    mes_90_perc: int | None


def calcular_probabilidade_contemplacao(
    num_cotas_grupo: int,
    prazo_meses: int,
    cotas_sorteadas_por_mes: int = 1,
) -> ResultadoProbabilidade:
    """
    Calcula a probabilidade mensal e acumulada de contemplação por sorteio
    para um participante específico, assumindo `cotas_sorteadas_por_mes`
    contemplações por assembleia e nenhuma saída antecipada do grupo (nem
    pelo próprio participante, nem por lances de terceiros).
    """
    if num_cotas_grupo <= 0 or prazo_meses <= 0:
        return ResultadoProbabilidade(meses=[], prob_mensal=[], prob_acumulada=[], mes_50_perc=None, mes_90_perc=None)

    meses = list(range(1, prazo_meses + 1))
    prob_mensal: list[float] = []
    prob_nao_contemplado_ainda = 1.0
    prob_acumulada: list[float] = []

    cotas_remanescentes = num_cotas_grupo
    for _ in meses:
        if cotas_remanescentes <= 0:
            p_mes = 0.0
        else:
            p_mes = min(cotas_sorteadas_por_mes / cotas_remanescentes, 1.0)

        p_contemplado_neste_mes = prob_nao_contemplado_ainda * p_mes
        prob_mensal.append(p_contemplado_neste_mes)
        prob_nao_contemplado_ainda *= (1 - p_mes)
        prob_acumulada.append(1 - prob_nao_contemplado_ainda)

        cotas_remanescentes = max(cotas_remanescentes - cotas_sorteadas_por_mes, 0)

    mes_50_perc = next((m for m, p in zip(meses, prob_acumulada) if p >= 0.5), None)
    mes_90_perc = next((m for m, p in zip(meses, prob_acumulada) if p >= 0.9), None)

    return ResultadoProbabilidade(
        meses=meses,
        prob_mensal=prob_mensal,
        prob_acumulada=prob_acumulada,
        mes_50_perc=mes_50_perc,
        mes_90_perc=mes_90_perc,
    )
