"""
Consórcio Imobiliário como Investimento (compra + locação).

Modela a estratégia de usar um consórcio para adquirir um imóvel e colocá-lo
para alugar, projetando o fluxo de caixa em 3 fases ao longo de um horizonte
total (padrão: 20 anos):

    Fase 1 — Pré-Contemplação: paga a parcela do consórcio, sem receita
    (ainda não há imóvel). Um lance pode antecipar a contemplação.

    Fase 2 — Locação + Parcelas: a partir da contemplação, o imóvel é
    alugado (gerando receita) enquanto as parcelas do consórcio continuam
    até o fim do prazo original do grupo.

    Fase 3 — Renda Líquida: após o consórcio quitado, sobra só a receita de
    aluguel (reajustada) até o fim do horizonte de simulação.

Metodologia inspirada em modelos de simulação de ROI de consórcio
imobiliário usados no mercado (ex.: yield de aluguel sobre o valor do
crédito, reajuste do aluguel pelo IPCA, valorização do imóvel separada do
reajuste do saldo devedor do consórcio).
"""

from dataclasses import dataclass, field

from src.calculations import ParcelaMensal, calcular_tir_mensal


@dataclass
class FaseInvestimento:
    nome: str
    mes_inicio: int
    mes_fim: int
    desembolso_total: float
    recebimento_total: float


@dataclass
class ResultadoInvestimentoImovel:
    horizonte_meses: int
    mes_contemplacao: int
    valor_lance: float
    itbi_escritura: float

    fase1: FaseInvestimento
    fase2: FaseInvestimento
    fase3: FaseInvestimento

    serie_meses: list[int]
    serie_fluxo_liquido: list[float]
    serie_patrimonio_acumulado: list[float]
    serie_aluguel: list[float]

    total_desembolsado: float
    alugueis_recebidos: float
    valor_imovel_final: float
    patrimonio_total: float
    roi_total_pct: float
    roi_anualizado_pct: float
    tir_mensal_pct: float | None
    tir_anual_pct: float | None
    tir_convergiu: bool


def _aluguel_no_mes(
    mes: int,
    mes_contemplacao: int,
    aluguel_inicial: float,
    reajuste_aluguel_anual: float,
) -> float:
    """Aluguel no mês `mes`, reajustado a cada 12 meses desde o início da locação."""
    meses_desde_locacao = mes - mes_contemplacao
    anos_completos = (meses_desde_locacao - 1) // 12 if meses_desde_locacao > 0 else 0
    return aluguel_inicial * ((1 + reajuste_aluguel_anual / 100) ** anos_completos)


def calcular_investimento_imovel(
    *,
    valor_credito: float,
    cronograma_consorcio: list[ParcelaMensal],
    prazo_meses: int,
    mes_contemplacao: int,
    perc_lance: float,
    tipo_lance: str,  # "proprio" ou "embutido"
    itbi_escritura_perc: float,
    manutencao_mensal: float,
    yield_aluguel_mensal: float,
    reajuste_aluguel_anual: float,
    valorizacao_imobiliaria_anual: float,
    horizonte_anos: int,
) -> ResultadoInvestimentoImovel:
    horizonte_meses = horizonte_anos * 12
    mes_contemplacao = max(1, min(mes_contemplacao, prazo_meses, horizonte_meses))

    valor_lance = valor_credito * (perc_lance / 100)
    itbi_escritura = valor_credito * (itbi_escritura_perc / 100)
    aluguel_inicial = valor_credito * (yield_aluguel_mensal / 100)

    def parcela_no_mes(m: int) -> float:
        if 1 <= m <= len(cronograma_consorcio):
            return cronograma_consorcio[m - 1].parcela
        return 0.0

    # ── Fase 1: Pré-Contemplação ──────────────────────────────────────────
    fase1_parcelas = sum(parcela_no_mes(m) for m in range(1, mes_contemplacao + 1))
    fase1 = FaseInvestimento(
        nome="Pré-Contemplação", mes_inicio=1, mes_fim=mes_contemplacao,
        desembolso_total=fase1_parcelas, recebimento_total=0.0,
    )

    # ── Fase 2: Locação + Parcelas (contemplação+1 até fim do prazo, limitado ao horizonte) ──
    fim_fase2 = min(prazo_meses, horizonte_meses)
    fase2_parcelas = sum(parcela_no_mes(m) for m in range(mes_contemplacao + 1, fim_fase2 + 1))
    fase2_manutencao = manutencao_mensal * max(fim_fase2 - mes_contemplacao, 0)
    fase2_alugueis = sum(
        _aluguel_no_mes(m, mes_contemplacao, aluguel_inicial, reajuste_aluguel_anual)
        for m in range(mes_contemplacao + 1, fim_fase2 + 1)
    )
    fase2 = FaseInvestimento(
        nome="Locação + Parcelas", mes_inicio=mes_contemplacao + 1, mes_fim=fim_fase2,
        desembolso_total=fase2_parcelas + fase2_manutencao, recebimento_total=fase2_alugueis,
    )

    # ── Fase 3: Renda Líquida (fim do prazo até o fim do horizonte) ───────
    fase3_alugueis = sum(
        _aluguel_no_mes(m, mes_contemplacao, aluguel_inicial, reajuste_aluguel_anual)
        for m in range(fim_fase2 + 1, horizonte_meses + 1)
    )
    fase3 = FaseInvestimento(
        nome="Renda Líquida", mes_inicio=fim_fase2 + 1, mes_fim=horizonte_meses,
        desembolso_total=0.0, recebimento_total=fase3_alugueis,
    )

    # ── Séries mensais completas (para gráfico) ───────────────────────────
    serie_meses = list(range(0, horizonte_meses + 1))
    serie_fluxo_liquido = [0.0]
    serie_aluguel = [0.0]
    serie_patrimonio_acumulado = [0.0]
    acumulado = 0.0
    lance_cash = valor_lance if tipo_lance == "proprio" else 0.0

    for m in range(1, horizonte_meses + 1):
        parcela = parcela_no_mes(m)
        manutencao = manutencao_mensal if (mes_contemplacao < m <= fim_fase2) else 0.0
        aluguel = _aluguel_no_mes(m, mes_contemplacao, aluguel_inicial, reajuste_aluguel_anual) if m > mes_contemplacao else 0.0
        extra = 0.0
        if m == mes_contemplacao:
            extra = -(lance_cash + itbi_escritura)
        fluxo_mes = -parcela - manutencao + aluguel + extra
        acumulado += fluxo_mes
        serie_fluxo_liquido.append(fluxo_mes)
        serie_aluguel.append(aluguel)
        serie_patrimonio_acumulado.append(acumulado)

    # ── Resumo financeiro ──────────────────────────────────────────────────
    total_desembolsado = fase1.desembolso_total + lance_cash + fase2.desembolso_total + itbi_escritura
    alugueis_recebidos = fase2.recebimento_total + fase3.recebimento_total
    valor_imovel_final = valor_credito * ((1 + valorizacao_imobiliaria_anual / 100) ** horizonte_anos)
    patrimonio_total = alugueis_recebidos + valor_imovel_final
    roi_total_pct = (patrimonio_total / total_desembolsado - 1) * 100 if total_desembolsado > 0 else 0.0
    roi_anualizado_pct = (
        ((1 + roi_total_pct / 100) ** (1 / horizonte_anos) - 1) * 100 if horizonte_anos > 0 else 0.0
    )

    # ── TIR do fluxo de caixa completo (inclui valor do imóvel no mês final) ──
    fluxos_tir = list(serie_fluxo_liquido[1:])  # remove mes 0
    if fluxos_tir:
        fluxos_tir[-1] += valor_imovel_final
    tir_mensal, convergiu = calcular_tir_mensal(fluxos_tir)
    tir_anual = ((1 + tir_mensal) ** 12 - 1) * 100 if (convergiu and tir_mensal is not None) else None

    return ResultadoInvestimentoImovel(
        horizonte_meses=horizonte_meses,
        mes_contemplacao=mes_contemplacao,
        valor_lance=valor_lance,
        itbi_escritura=itbi_escritura,
        fase1=fase1, fase2=fase2, fase3=fase3,
        serie_meses=serie_meses,
        serie_fluxo_liquido=serie_fluxo_liquido,
        serie_patrimonio_acumulado=serie_patrimonio_acumulado,
        serie_aluguel=serie_aluguel,
        total_desembolsado=total_desembolsado,
        alugueis_recebidos=alugueis_recebidos,
        valor_imovel_final=valor_imovel_final,
        patrimonio_total=patrimonio_total,
        roi_total_pct=roi_total_pct,
        roi_anualizado_pct=roi_anualizado_pct,
        tir_mensal_pct=(tir_mensal * 100 if tir_mensal is not None else None),
        tir_anual_pct=tir_anual,
        tir_convergiu=convergiu,
    )
