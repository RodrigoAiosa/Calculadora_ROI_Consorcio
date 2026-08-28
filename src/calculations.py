"""
Núcleo de cálculo financeiro da Calculadora de ROI de Consórcio.

Contém as 3 comparações da ferramenta:
    1. Consórcio x Financiamento (Tabela Price)
    2. Consórcio x Investir e comprar à vista
    3. Lance / contemplação antecipada

Todas as funções são puras (sem I/O, sem Streamlit) para facilitar testes
unitários e reuso fora da interface web.
"""

import math
from dataclasses import dataclass, field


# ─────────────────────────────────────────────────────────────────────────────
# Consórcio
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class ResultadoConsorcio:
    parcela: float
    custo_total: float


def calcular_consorcio(
    valor_credito: float,
    prazo_meses: int,
    taxa_adm: float,
    fundo_reserva: float,
    seguro_perc: float,
) -> ResultadoConsorcio:
    """Parcela e custo total do consórcio (amortização linear + seguro mensal)."""
    custo_adm_total = valor_credito * (taxa_adm / 100)
    custo_fundo_total = valor_credito * (fundo_reserva / 100)
    parcela_base = (valor_credito + custo_adm_total + custo_fundo_total) / prazo_meses
    seguro_mensal_val = valor_credito * (seguro_perc / 100)
    parcela = parcela_base + seguro_mensal_val
    custo_total = parcela * prazo_meses
    return ResultadoConsorcio(parcela=parcela, custo_total=custo_total)


# ─────────────────────────────────────────────────────────────────────────────
# Financiamento (Tabela Price)
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class ResultadoFinanciamento:
    parcela: float
    custo_total: float
    economia_consorcio: float
    economia_consorcio_perc: float


def calcular_financiamento(
    valor_credito: float,
    taxa_financiamento: float,
    prazo_meses: int,
    custo_total_consorcio: float,
) -> ResultadoFinanciamento:
    """Parcela pelo sistema Price e comparação direta com o custo do consórcio."""
    i = taxa_financiamento / 100
    if i == 0:
        parcela = valor_credito / prazo_meses
    else:
        parcela = valor_credito * (i * (1 + i) ** prazo_meses) / ((1 + i) ** prazo_meses - 1)
    custo_total = parcela * prazo_meses
    economia = custo_total - custo_total_consorcio
    economia_perc = (economia / custo_total * 100) if custo_total > 0 else 0.0
    return ResultadoFinanciamento(
        parcela=parcela,
        custo_total=custo_total,
        economia_consorcio=economia,
        economia_consorcio_perc=economia_perc,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Investir e comprar à vista
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class ResultadoInvestimento:
    meses: list[int]
    serie_investido: list[float]
    serie_bem_corrigido: list[float]
    mes_cruzamento: int | None
    ganho_final: float


def calcular_investimento(
    parcela_consorcio: float,
    valor_credito: float,
    taxa_investimento: float,
    correcao_bem: float,
    prazo_meses: int,
) -> ResultadoInvestimento:
    """
    Simula investir mensalmente o valor da parcela do consórcio (renda fixa,
    juros compostos) em vez de entrar no grupo, comparando com o valor do
    bem corrigido (valorização/inflação) mês a mês.
    """
    i_inv = taxa_investimento / 100
    i_cor = correcao_bem / 100
    meses = list(range(0, prazo_meses + 1))

    def valor_investido_ate(m: int) -> float:
        if i_inv == 0:
            return parcela_consorcio * m
        return parcela_consorcio * (((1 + i_inv) ** m - 1) / i_inv)

    def valor_bem_corrigido_ate(m: int) -> float:
        return valor_credito * ((1 + i_cor) ** m)

    serie_investido = [valor_investido_ate(m) for m in meses]
    serie_bem_corrigido = [valor_bem_corrigido_ate(m) for m in meses]

    mes_cruzamento = None
    for m in meses:
        if serie_investido[m] >= serie_bem_corrigido[m]:
            mes_cruzamento = m
            break

    ganho_final = serie_investido[-1] - serie_bem_corrigido[-1]

    return ResultadoInvestimento(
        meses=meses,
        serie_investido=serie_investido,
        serie_bem_corrigido=serie_bem_corrigido,
        mes_cruzamento=mes_cruzamento,
        ganho_final=ganho_final,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Lance / contemplação antecipada
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class ResultadoLance:
    valor_lance: float
    prazo_final_com_lance: int
    meses_antecipados: int
    beneficio_valorizacao_evitada: float
    custo_oportunidade_lance: float
    ganho_liquido: float
    serie_saldo_sem_lance: list[float] = field(default_factory=list)
    serie_saldo_com_lance: list[float] = field(default_factory=list)


def calcular_lance(
    parcela_consorcio: float,
    valor_credito: float,
    perc_lance: float,
    mes_lance: int,
    prazo_meses: int,
    taxa_investimento: float,
    correcao_bem: float,
) -> ResultadoLance:
    """
    Simula a oferta de um lance no mês `mes_lance`, reduzindo o prazo restante
    (mantendo a parcela). Compara o benefício de antecipar a compra (valorização
    do bem evitada) contra o custo de oportunidade do dinheiro do lance
    (o que renderia se ficasse investido até o fim do prazo original).
    """
    i_inv = taxa_investimento / 100
    i_cor = correcao_bem / 100
    meses = list(range(0, prazo_meses + 1))

    valor_lance = valor_credito * (perc_lance / 100)
    saldo_no_momento = parcela_consorcio * (prazo_meses - mes_lance)
    saldo_apos_lance = max(saldo_no_momento - valor_lance, 0.0)
    parcelas_restantes_novas = (
        math.ceil(saldo_apos_lance / parcela_consorcio) if parcela_consorcio > 0 else 0
    )
    prazo_final_com_lance = min(mes_lance + parcelas_restantes_novas, prazo_meses)
    meses_antecipados = max(prazo_meses - prazo_final_com_lance, 0)

    beneficio_valorizacao_evitada = valor_credito * ((1 + i_cor) ** meses_antecipados - 1)
    if i_inv > 0:
        custo_oportunidade_lance = valor_lance * ((1 + i_inv) ** (prazo_meses - mes_lance) - 1)
    else:
        custo_oportunidade_lance = 0.0
    ganho_liquido = beneficio_valorizacao_evitada - custo_oportunidade_lance

    serie_saldo_sem_lance = [parcela_consorcio * (prazo_meses - m) for m in meses]
    serie_saldo_com_lance = []
    for m in meses:
        if m < mes_lance:
            serie_saldo_com_lance.append(parcela_consorcio * (prazo_meses - m))
        elif m == mes_lance:
            serie_saldo_com_lance.append(saldo_apos_lance)
        else:
            restante = saldo_apos_lance - parcela_consorcio * (m - mes_lance)
            serie_saldo_com_lance.append(max(restante, 0.0))

    return ResultadoLance(
        valor_lance=valor_lance,
        prazo_final_com_lance=prazo_final_com_lance,
        meses_antecipados=meses_antecipados,
        beneficio_valorizacao_evitada=beneficio_valorizacao_evitada,
        custo_oportunidade_lance=custo_oportunidade_lance,
        ganho_liquido=ganho_liquido,
        serie_saldo_sem_lance=serie_saldo_sem_lance,
        serie_saldo_com_lance=serie_saldo_com_lance,
    )
