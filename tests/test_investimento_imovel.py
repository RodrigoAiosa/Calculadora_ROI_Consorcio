"""Testes unitários do módulo de consórcio imobiliário como investimento."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.calculations import calcular_consorcio
from src.investimento_imovel import calcular_investimento_imovel


def _consorcio_padrao():
    return calcular_consorcio(
        valor_credito=500000, prazo_meses=200, taxa_adm=18, fundo_reserva=2,
        seguro_perc=0.0, reajuste_anual=0.0, seguro_sobre_saldo=False,
    )


def test_fase1_bate_com_parcelas_ate_contemplacao():
    consorcio = _consorcio_padrao()
    r = calcular_investimento_imovel(
        valor_credito=500000, cronograma_consorcio=consorcio.cronograma, prazo_meses=200,
        mes_contemplacao=24, perc_lance=30.0, tipo_lance="embutido",
        itbi_escritura_perc=4.0, manutencao_mensal=400.0,
        yield_aluguel_mensal=0.45, reajuste_aluguel_anual=4.5,
        valorizacao_imobiliaria_anual=5.0, horizonte_anos=20,
    )
    assert round(r.fase1.desembolso_total, 2) == round(consorcio.parcela_inicial * 24, 2)
    assert r.fase1.recebimento_total == 0.0
    assert r.fase1.mes_inicio == 1
    assert r.fase1.mes_fim == 24


def test_lance_embutido_nao_gera_desembolso_de_lance():
    consorcio = _consorcio_padrao()
    r = calcular_investimento_imovel(
        valor_credito=500000, cronograma_consorcio=consorcio.cronograma, prazo_meses=200,
        mes_contemplacao=24, perc_lance=30.0, tipo_lance="embutido",
        itbi_escritura_perc=4.0, manutencao_mensal=400.0,
        yield_aluguel_mensal=0.45, reajuste_aluguel_anual=4.5,
        valorizacao_imobiliaria_anual=5.0, horizonte_anos=20,
    )
    assert r.valor_lance == 150000.0
    # total desembolsado nao deve incluir o valor do lance (embutido = sem desembolso de bolso)
    assert round(r.total_desembolsado, 2) == round(r.fase1.desembolso_total + r.fase2.desembolso_total + r.itbi_escritura, 2)


def test_lance_proprio_soma_ao_desembolso():
    consorcio = _consorcio_padrao()
    r = calcular_investimento_imovel(
        valor_credito=500000, cronograma_consorcio=consorcio.cronograma, prazo_meses=200,
        mes_contemplacao=24, perc_lance=30.0, tipo_lance="proprio",
        itbi_escritura_perc=4.0, manutencao_mensal=400.0,
        yield_aluguel_mensal=0.45, reajuste_aluguel_anual=4.5,
        valorizacao_imobiliaria_anual=5.0, horizonte_anos=20,
    )
    esperado = r.fase1.desembolso_total + r.fase2.desembolso_total + r.itbi_escritura + r.valor_lance
    assert round(r.total_desembolsado, 2) == round(esperado, 2)


def test_valor_imovel_final_usa_valorizacao_composta():
    consorcio = _consorcio_padrao()
    r = calcular_investimento_imovel(
        valor_credito=500000, cronograma_consorcio=consorcio.cronograma, prazo_meses=200,
        mes_contemplacao=24, perc_lance=30.0, tipo_lance="embutido",
        itbi_escritura_perc=4.0, manutencao_mensal=400.0,
        yield_aluguel_mensal=0.45, reajuste_aluguel_anual=4.5,
        valorizacao_imobiliaria_anual=5.0, horizonte_anos=20,
    )
    esperado = 500000 * (1.05 ** 20)
    assert abs(r.valor_imovel_final - esperado) < 0.01


def test_patrimonio_total_e_alugueis_mais_imovel():
    consorcio = _consorcio_padrao()
    r = calcular_investimento_imovel(
        valor_credito=500000, cronograma_consorcio=consorcio.cronograma, prazo_meses=200,
        mes_contemplacao=24, perc_lance=30.0, tipo_lance="embutido",
        itbi_escritura_perc=4.0, manutencao_mensal=400.0,
        yield_aluguel_mensal=0.45, reajuste_aluguel_anual=4.5,
        valorizacao_imobiliaria_anual=5.0, horizonte_anos=20,
    )
    assert abs(r.patrimonio_total - (r.alugueis_recebidos + r.valor_imovel_final)) < 0.01


def test_roi_total_consistente_com_patrimonio_e_desembolso():
    consorcio = _consorcio_padrao()
    r = calcular_investimento_imovel(
        valor_credito=500000, cronograma_consorcio=consorcio.cronograma, prazo_meses=200,
        mes_contemplacao=24, perc_lance=30.0, tipo_lance="embutido",
        itbi_escritura_perc=4.0, manutencao_mensal=400.0,
        yield_aluguel_mensal=0.45, reajuste_aluguel_anual=4.5,
        valorizacao_imobiliaria_anual=5.0, horizonte_anos=20,
    )
    esperado = (r.patrimonio_total / r.total_desembolsado - 1) * 100
    assert abs(r.roi_total_pct - esperado) < 0.01


def test_fase3_comeca_apos_fim_do_prazo_e_nao_tem_desembolso():
    consorcio = _consorcio_padrao()
    r = calcular_investimento_imovel(
        valor_credito=500000, cronograma_consorcio=consorcio.cronograma, prazo_meses=200,
        mes_contemplacao=24, perc_lance=30.0, tipo_lance="embutido",
        itbi_escritura_perc=4.0, manutencao_mensal=400.0,
        yield_aluguel_mensal=0.45, reajuste_aluguel_anual=4.5,
        valorizacao_imobiliaria_anual=5.0, horizonte_anos=20,
    )
    assert r.fase3.mes_inicio == 201
    assert r.fase3.mes_fim == 240
    assert r.fase3.desembolso_total == 0.0
    assert r.fase3.recebimento_total > 0


def test_serie_mensal_tem_tamanho_correto():
    consorcio = _consorcio_padrao()
    r = calcular_investimento_imovel(
        valor_credito=500000, cronograma_consorcio=consorcio.cronograma, prazo_meses=200,
        mes_contemplacao=24, perc_lance=30.0, tipo_lance="embutido",
        itbi_escritura_perc=4.0, manutencao_mensal=400.0,
        yield_aluguel_mensal=0.45, reajuste_aluguel_anual=4.5,
        valorizacao_imobiliaria_anual=5.0, horizonte_anos=20,
    )
    assert len(r.serie_meses) == 241  # mes 0 a 240
    assert len(r.serie_fluxo_liquido) == 241
    assert len(r.serie_patrimonio_acumulado) == 241


def test_mes_contemplacao_fora_do_prazo_e_ajustado():
    consorcio = _consorcio_padrao()
    r = calcular_investimento_imovel(
        valor_credito=500000, cronograma_consorcio=consorcio.cronograma, prazo_meses=200,
        mes_contemplacao=999, perc_lance=30.0, tipo_lance="embutido",
        itbi_escritura_perc=4.0, manutencao_mensal=400.0,
        yield_aluguel_mensal=0.45, reajuste_aluguel_anual=4.5,
        valorizacao_imobiliaria_anual=5.0, horizonte_anos=20,
    )
    assert r.mes_contemplacao == 200


def test_tir_converge_no_cenario_padrao():
    consorcio = _consorcio_padrao()
    r = calcular_investimento_imovel(
        valor_credito=500000, cronograma_consorcio=consorcio.cronograma, prazo_meses=200,
        mes_contemplacao=24, perc_lance=30.0, tipo_lance="embutido",
        itbi_escritura_perc=4.0, manutencao_mensal=400.0,
        yield_aluguel_mensal=0.45, reajuste_aluguel_anual=4.5,
        valorizacao_imobiliaria_anual=5.0, horizonte_anos=20,
    )
    assert r.tir_convergiu
    assert r.tir_anual_pct is not None
    assert r.tir_anual_pct > 0


def test_horizonte_menor_que_prazo_nao_ultrapassa_a_serie_mensal():
    """
    Regressão: se o horizonte de simulação (ex: 10 anos = 120 meses) termina
    ANTES do fim do prazo do consórcio (ex: 200 meses), a Fase 2 não pode
    somar parcelas/aluguéis além do mês 120 — senão os totais ficam
    inconsistentes com a série mensal, que para no horizonte.
    """
    consorcio = _consorcio_padrao()  # prazo_meses=200
    r = calcular_investimento_imovel(
        valor_credito=500000, cronograma_consorcio=consorcio.cronograma, prazo_meses=200,
        mes_contemplacao=24, perc_lance=30.0, tipo_lance="embutido",
        itbi_escritura_perc=4.0, manutencao_mensal=400.0,
        yield_aluguel_mensal=0.45, reajuste_aluguel_anual=4.5,
        valorizacao_imobiliaria_anual=5.0, horizonte_anos=10,  # 120 meses < prazo de 200
    )
    assert r.horizonte_meses == 120
    assert r.fase2.mes_fim == 120  # nao deve ultrapassar o horizonte
    assert r.fase3.desembolso_total == 0.0
    assert r.fase3.recebimento_total == 0.0  # fase 3 nao deve existir (horizonte acaba antes do prazo)
    assert len(r.serie_meses) == 121

    # o total desembolsado nao pode contar parcelas alem do mes 120
    parcelas_ate_120 = sum(p.parcela for p in consorcio.cronograma[:120])
    manutencao_esperada = 400.0 * (120 - 24)
    assert abs(r.fase1.desembolso_total + r.fase2.desembolso_total - parcelas_ate_120 - manutencao_esperada) < 0.01
