"""
Núcleo de cálculo financeiro da Calculadora de ROI de Consórcio.

Contém o motor de cronograma detalhado do consórcio e as 4 comparações da
ferramenta:
    1. Consórcio x Financiamento (Tabela Price)
    2. Consórcio x Investir e comprar à vista
    3. Lance / contemplação antecipada (próprio ou embutido)
    4. CET (Custo Efetivo Total) do consórcio

Todas as funções são puras (sem I/O, sem Streamlit) para facilitar testes
unitários e reuso fora da interface web.

Premissas do motor detalhado (`gerar_cronograma_consorcio`):
    - A administração + fundo de reserva são diluídos linearmente sobre o
      saldo devedor original.
    - A cada 12 meses (aniversário do grupo), o saldo devedor remanescente
      e o valor do crédito são reajustados pelo índice informado
      (tipicamente INCC para imóveis, IPCA para veículos/bens em geral),
      e a parcela é recalculada dividindo o novo saldo pelos meses
      restantes.
    - O seguro pode incidir sobre o saldo devedor remanescente (modelo
      detalhado, mais realista) ou sobre o valor do crédito original
      (modelo simplificado, `reajuste_anual=0` e `seguro_sobre_saldo=False`
      reproduz o comportamento da v1 desta calculadora).
"""

import math
from dataclasses import dataclass, field
from typing import Literal


# ─────────────────────────────────────────────────────────────────────────────
# Cronograma detalhado do consórcio
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class ParcelaMensal:
    mes: int
    saldo_devedor_antes: float
    parcela: float
    seguro: float
    valor_credito_atual: float
    saldo_devedor_depois: float


def gerar_cronograma_consorcio(
    valor_credito: float,
    prazo_meses: int,
    taxa_adm: float,
    fundo_reserva: float,
    seguro_perc: float,
    reajuste_anual: float = 0.0,
    seguro_sobre_saldo: bool = True,
) -> list[ParcelaMensal]:
    """Gera o cronograma mês a mês do consórcio (ver premissas no docstring do módulo)."""
    if prazo_meses <= 0:
        return []

    saldo_restante = valor_credito * (1 + taxa_adm / 100 + fundo_reserva / 100)
    valor_credito_atual = valor_credito
    parcela_atual = saldo_restante / prazo_meses

    cronograma: list[ParcelaMensal] = []
    for mes in range(1, prazo_meses + 1):
        # Reajuste anual no aniversário do grupo (a cada 12 meses corridos)
        if reajuste_anual and mes > 1 and (mes - 1) % 12 == 0:
            fator = 1 + reajuste_anual / 100
            saldo_restante *= fator
            valor_credito_atual *= fator
            meses_restantes = prazo_meses - mes + 1
            parcela_atual = saldo_restante / meses_restantes if meses_restantes > 0 else 0.0

        base_seguro = saldo_restante if seguro_sobre_saldo else valor_credito_atual
        seguro_mes = base_seguro * (seguro_perc / 100)
        parcela_total = parcela_atual + seguro_mes

        saldo_antes = saldo_restante
        saldo_restante = max(saldo_restante - parcela_atual, 0.0)

        cronograma.append(ParcelaMensal(
            mes=mes,
            saldo_devedor_antes=saldo_antes,
            parcela=parcela_total,
            seguro=seguro_mes,
            valor_credito_atual=valor_credito_atual,
            saldo_devedor_depois=saldo_restante,
        ))
    return cronograma


@dataclass
class ResultadoConsorcio:
    cronograma: list[ParcelaMensal]
    parcela_media: float
    parcela_inicial: float
    custo_total: float

    @property
    def parcelas(self) -> list[float]:
        return [p.parcela for p in self.cronograma]


def calcular_consorcio(
    valor_credito: float,
    prazo_meses: int,
    taxa_adm: float,
    fundo_reserva: float,
    seguro_perc: float,
    reajuste_anual: float = 0.0,
    seguro_sobre_saldo: bool = True,
) -> ResultadoConsorcio:
    """Calcula o cronograma completo e agrega os totais do consórcio."""
    cronograma = gerar_cronograma_consorcio(
        valor_credito, prazo_meses, taxa_adm, fundo_reserva, seguro_perc,
        reajuste_anual=reajuste_anual, seguro_sobre_saldo=seguro_sobre_saldo,
    )
    if not cronograma:
        return ResultadoConsorcio(cronograma=[], parcela_media=0.0, parcela_inicial=0.0, custo_total=0.0)

    custo_total = sum(p.parcela for p in cronograma)
    parcela_media = custo_total / len(cronograma)
    parcela_inicial = cronograma[0].parcela
    return ResultadoConsorcio(
        cronograma=cronograma,
        parcela_media=parcela_media,
        parcela_inicial=parcela_inicial,
        custo_total=custo_total,
    )


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
    if prazo_meses <= 0:
        return ResultadoFinanciamento(parcela=0.0, custo_total=0.0, economia_consorcio=0.0, economia_consorcio_perc=0.0)

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
    parcelas: list[float],
    valor_credito: float,
    taxa_investimento: float,
    correcao_bem: float,
    prazo_meses: int,
) -> ResultadoInvestimento:
    """
    Simula investir mensalmente o valor da parcela do consórcio (juros
    compostos) em vez de entrar no grupo, comparando com o valor do bem
    corrigido (valorização/inflação estimada) mês a mês. Aceita uma parcela
    diferente por mês (`parcelas`), pois com reajuste anual ela pode variar.
    """
    if prazo_meses <= 0 or not parcelas:
        return ResultadoInvestimento(meses=[0], serie_investido=[0.0], serie_bem_corrigido=[valor_credito], mes_cruzamento=None, ganho_final=-valor_credito)

    i_inv = taxa_investimento / 100
    i_cor = correcao_bem / 100
    meses = list(range(0, prazo_meses + 1))

    serie_investido = [0.0]
    saldo = 0.0
    for m in range(1, prazo_meses + 1):
        saldo = saldo * (1 + i_inv) + parcelas[m - 1]
        serie_investido.append(saldo)

    serie_bem_corrigido = [valor_credito * ((1 + i_cor) ** m) for m in meses]

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
# Lance / contemplação antecipada (próprio ou embutido)
# ─────────────────────────────────────────────────────────────────────────────
TipoLance = Literal["proprio", "embutido"]


@dataclass
class ResultadoLance:
    tipo: TipoLance
    valor_lance: float
    credito_liquido_recebido: float
    prazo_final_com_lance: int
    meses_antecipados: int
    beneficio_valorizacao_evitada: float
    custo_oportunidade_lance: float
    ganho_liquido: float
    serie_saldo_sem_lance: list[float] = field(default_factory=list)
    serie_saldo_com_lance: list[float] = field(default_factory=list)


def calcular_lance(
    cronograma: list[ParcelaMensal],
    perc_lance: float,
    mes_lance: int,
    prazo_meses: int,
    taxa_investimento: float,
    correcao_bem: float,
    tipo_lance: TipoLance = "proprio",
) -> ResultadoLance:
    """
    Simula a oferta de um lance no mês `mes_lance`, reduzindo o prazo
    restante (mantendo a parcela recalculada).

    - **Lance próprio**: dinheiro extra do bolso do participante. Reduz o
      saldo devedor; o crédito recebido permanece integral; o "custo" é o
      que esse dinheiro renderia se ficasse investido até o fim do prazo
      original (custo de oportunidade).
    - **Lance embutido**: parte do próprio crédito é usada como lance
      (financiado pelo fundo comum do grupo). Não há desembolso extra do
      participante, mas o crédito líquido recebido é menor.
    """
    if not cronograma or mes_lance < 1 or mes_lance > prazo_meses:
        return ResultadoLance(
            tipo=tipo_lance, valor_lance=0.0, credito_liquido_recebido=0.0,
            prazo_final_com_lance=prazo_meses, meses_antecipados=0,
            beneficio_valorizacao_evitada=0.0, custo_oportunidade_lance=0.0, ganho_liquido=0.0,
        )

    i_inv = taxa_investimento / 100
    i_cor = correcao_bem / 100
    meses = list(range(0, prazo_meses + 1))

    ref = cronograma[mes_lance - 1]
    valor_credito_no_mes = ref.valor_credito_atual
    saldo_no_momento = ref.saldo_devedor_antes
    parcela_no_momento = ref.parcela

    valor_lance = valor_credito_no_mes * (perc_lance / 100)
    saldo_apos_lance = max(saldo_no_momento - valor_lance, 0.0)
    parcelas_restantes_novas = math.ceil(saldo_apos_lance / parcela_no_momento) if parcela_no_momento > 0 else 0
    prazo_final_com_lance = min(mes_lance + parcelas_restantes_novas, prazo_meses)
    meses_antecipados = max(prazo_meses - prazo_final_com_lance, 0)

    if tipo_lance == "proprio":
        credito_liquido_recebido = valor_credito_no_mes
        custo_oportunidade_lance = (
            valor_lance * ((1 + i_inv) ** (prazo_meses - mes_lance) - 1) if i_inv > 0 else 0.0
        )
    else:  # embutido
        credito_liquido_recebido = max(valor_credito_no_mes - valor_lance, 0.0)
        custo_oportunidade_lance = 0.0  # sem desembolso extra do participante

    beneficio_valorizacao_evitada = credito_liquido_recebido * ((1 + i_cor) ** meses_antecipados - 1)
    ganho_liquido = beneficio_valorizacao_evitada - custo_oportunidade_lance

    serie_saldo_sem_lance = [0.0] + [p.saldo_devedor_depois for p in cronograma]
    # reconstitui saldo devedor "com lance": igual até mes_lance, cai o valor do
    # lance naquele mês, depois amortiza pela parcela original até zerar.
    serie_saldo_com_lance = []
    for m in meses:
        if m < mes_lance:
            serie_saldo_com_lance.append(serie_saldo_sem_lance[m])
        elif m == mes_lance:
            serie_saldo_com_lance.append(saldo_apos_lance)
        else:
            restante = saldo_apos_lance - parcela_no_momento * (m - mes_lance)
            serie_saldo_com_lance.append(max(restante, 0.0))

    return ResultadoLance(
        tipo=tipo_lance,
        valor_lance=valor_lance,
        credito_liquido_recebido=credito_liquido_recebido,
        prazo_final_com_lance=prazo_final_com_lance,
        meses_antecipados=meses_antecipados,
        beneficio_valorizacao_evitada=beneficio_valorizacao_evitada,
        custo_oportunidade_lance=custo_oportunidade_lance,
        ganho_liquido=ganho_liquido,
        serie_saldo_sem_lance=serie_saldo_sem_lance,
        serie_saldo_com_lance=serie_saldo_com_lance,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CET — Custo Efetivo Total
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class ResultadoCET:
    cet_mensal: float | None
    cet_anual: float | None
    mes_contemplacao: int
    convergiu: bool


def _npv(taxa_mensal: float, fluxos: list[float]) -> float:
    """Valor presente líquido de uma lista de fluxos mensais (índice 0 = mês 1)."""
    return sum(cf / (1 + taxa_mensal) ** (t + 1) for t, cf in enumerate(fluxos))


def calcular_cet(
    parcelas: list[float],
    valor_credito_recebido: float,
    mes_contemplacao: int,
) -> ResultadoCET:
    """
    Calcula o Custo Efetivo Total (CET) mensal e anualizado do consórcio via
    TIR (taxa interna de retorno) do fluxo de caixa do participante:
    paga a parcela todo mês e recebe o crédito no mês da contemplação.

    Por padrão, recomenda-se `mes_contemplacao = prazo_meses` (cenário mais
    conservador — quem só é contemplado no último mês do grupo), que é a
    prática usual de divulgação de CET no mercado de consórcios.

    Retorna `convergiu=False` quando não foi encontrada raiz no intervalo de
    busca (fluxo de caixa atípico) — nesse caso o CET não deve ser exibido.
    """
    n = len(parcelas)
    if n == 0 or mes_contemplacao < 1 or mes_contemplacao > n:
        return ResultadoCET(cet_mensal=None, cet_anual=None, mes_contemplacao=mes_contemplacao, convergiu=False)

    fluxos = [-p for p in parcelas]
    fluxos[mes_contemplacao - 1] += valor_credito_recebido

    # Varredura para localizar um intervalo com troca de sinal do NPV.
    pontos = [i / 100 for i in range(-90, 500, 1)]  # -90% a +500% a.m., passo 1%
    anterior_i, anterior_npv = pontos[0], _npv(pontos[0], fluxos)
    intervalo = None
    for i in pontos[1:]:
        atual_npv = _npv(i, fluxos)
        if anterior_npv == 0:
            intervalo = (anterior_i, anterior_i)
            break
        if (anterior_npv < 0) != (atual_npv < 0):
            intervalo = (anterior_i, i)
            break
        anterior_i, anterior_npv = i, atual_npv

    if intervalo is None:
        return ResultadoCET(cet_mensal=None, cet_anual=None, mes_contemplacao=mes_contemplacao, convergiu=False)

    lo, hi = intervalo
    if lo == hi:
        cet_mensal = lo
    else:
        for _ in range(200):
            mid = (lo + hi) / 2
            npv_mid = _npv(mid, fluxos)
            npv_lo = _npv(lo, fluxos)
            if (npv_lo < 0) == (npv_mid < 0):
                lo = mid
            else:
                hi = mid
        cet_mensal = (lo + hi) / 2

    cet_anual = (1 + cet_mensal) ** 12 - 1
    return ResultadoCET(cet_mensal=cet_mensal * 100, cet_anual=cet_anual * 100, mes_contemplacao=mes_contemplacao, convergiu=True)
