"""Testes unitários dos cálculos financeiros (sem dependência do Streamlit)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.calculations import calcular_cet, calcular_consorcio, calcular_financiamento, calcular_investimento, calcular_lance


def test_calcular_consorcio_modo_simplificado_reproduz_v1():
    """reajuste=0 e seguro_sobre_saldo=False deve reproduzir a v1 (parcela constante)."""
    r = calcular_consorcio(60000, 60, 17, 2, 0.04, reajuste_anual=0.0, seguro_sobre_saldo=False)
    assert round(r.parcela_inicial, 2) == 1214.0
    assert round(r.custo_total, 2) == 72840.0
    parcelas_unicas = {round(p.parcela, 4) for p in r.cronograma}
    assert len(parcelas_unicas) == 1, "parcela deveria ser constante no modo simplificado"


def test_calcular_consorcio_prazo_zero_nao_quebra():
    r = calcular_consorcio(60000, 0, 17, 2, 0.04)
    assert r.cronograma == []
    assert r.custo_total == 0.0
    assert r.parcela_inicial == 0.0


def test_calcular_consorcio_reajuste_aumenta_parcela_apos_aniversario():
    r = calcular_consorcio(60000, 60, 17, 2, 0.04, reajuste_anual=6.0, seguro_sobre_saldo=True)
    assert r.cronograma[12].parcela > r.cronograma[0].parcela, "parcela deveria subir apos o reajuste do mes 13"
    assert r.custo_total > 72840.0, "custo total com reajuste deve ser maior que o modo simplificado"


def test_calcular_consorcio_seguro_sobre_saldo_decrescente():
    r = calcular_consorcio(60000, 60, 17, 2, 0.10, reajuste_anual=0.0, seguro_sobre_saldo=True)
    assert r.cronograma[0].seguro > r.cronograma[-1].seguro, "seguro deveria cair conforme o saldo devedor diminui"


def test_calcular_financiamento_price():
    consorcio = calcular_consorcio(60000, 60, 17, 2, 0.04, reajuste_anual=0.0, seguro_sobre_saldo=False)
    r = calcular_financiamento(
        valor_credito=60000, taxa_financiamento=1.7, prazo_meses=60,
        custo_total_consorcio=consorcio.custo_total,
    )
    assert round(r.parcela, 2) == 1603.02
    assert r.economia_consorcio > 0


def test_calcular_financiamento_taxa_zero():
    r = calcular_financiamento(valor_credito=12000, taxa_financiamento=0, prazo_meses=12, custo_total_consorcio=12000)
    assert round(r.parcela, 2) == 1000.0


def test_calcular_financiamento_prazo_zero_nao_quebra():
    r = calcular_financiamento(valor_credito=12000, taxa_financiamento=1.5, prazo_meses=0, custo_total_consorcio=0)
    assert r.parcela == 0.0
    assert r.custo_total == 0.0


def test_calcular_investimento_encontra_cruzamento():
    consorcio = calcular_consorcio(60000, 60, 17, 2, 0.04, reajuste_anual=0.0, seguro_sobre_saldo=False)
    r = calcular_investimento(
        parcelas=consorcio.parcelas, valor_credito=60000,
        taxa_investimento=0.85, correcao_bem=0.35, prazo_meses=60,
    )
    assert r.mes_cruzamento is not None
    assert r.mes_cruzamento <= 60
    assert r.serie_investido[r.mes_cruzamento] >= r.serie_bem_corrigido[r.mes_cruzamento]


def test_calcular_investimento_sem_cruzamento_quando_correcao_alta():
    consorcio = calcular_consorcio(60000, 60, 17, 2, 0.04, reajuste_anual=0.0, seguro_sobre_saldo=False)
    r = calcular_investimento(
        parcelas=consorcio.parcelas, valor_credito=60000,
        taxa_investimento=0.1, correcao_bem=5.0, prazo_meses=60,
    )
    assert r.mes_cruzamento is None
    assert r.ganho_final < 0


def test_calcular_investimento_aceita_parcelas_variaveis():
    """Com reajuste anual, as parcelas variam mes a mes; o motor deve suportar isso."""
    consorcio = calcular_consorcio(60000, 60, 17, 2, 0.04, reajuste_anual=6.0, seguro_sobre_saldo=True)
    r = calcular_investimento(
        parcelas=consorcio.parcelas, valor_credito=60000,
        taxa_investimento=0.85, correcao_bem=0.35, prazo_meses=60,
    )
    assert len(r.serie_investido) == 61


def test_calcular_lance_proprio_reduz_prazo():
    consorcio = calcular_consorcio(60000, 60, 17, 2, 0.04, reajuste_anual=0.0, seguro_sobre_saldo=False)
    r = calcular_lance(
        cronograma=consorcio.cronograma, perc_lance=25, mes_lance=12, prazo_meses=60,
        taxa_investimento=0.85, correcao_bem=0.35, tipo_lance="proprio",
    )
    assert r.prazo_final_com_lance < 60
    assert r.meses_antecipados > 0
    assert r.valor_lance == 15000.0
    assert r.credito_liquido_recebido == 60000.0, "lance proprio nao deve reduzir o credito recebido"
    assert r.custo_oportunidade_lance > 0


def test_calcular_lance_embutido_reduz_credito_liquido():
    consorcio = calcular_consorcio(60000, 60, 17, 2, 0.04, reajuste_anual=0.0, seguro_sobre_saldo=False)
    r = calcular_lance(
        cronograma=consorcio.cronograma, perc_lance=25, mes_lance=12, prazo_meses=60,
        taxa_investimento=0.85, correcao_bem=0.35, tipo_lance="embutido",
    )
    assert r.credito_liquido_recebido == 45000.0
    assert r.custo_oportunidade_lance == 0.0, "lance embutido nao gera custo de oportunidade (sem desembolso)"


def test_calcular_lance_quita_tudo():
    consorcio = calcular_consorcio(60000, 60, 17, 2, 0.04, reajuste_anual=0.0, seguro_sobre_saldo=False)
    r = calcular_lance(
        cronograma=consorcio.cronograma, perc_lance=100, mes_lance=12, prazo_meses=60,
        taxa_investimento=0.85, correcao_bem=0.35, tipo_lance="proprio",
    )
    assert r.prazo_final_com_lance == 12
    assert r.meses_antecipados == 48


def test_calcular_lance_mes_invalido_nao_quebra():
    consorcio = calcular_consorcio(60000, 60, 17, 2, 0.04)
    r = calcular_lance(
        cronograma=consorcio.cronograma, perc_lance=25, mes_lance=0, prazo_meses=60,
        taxa_investimento=0.85, correcao_bem=0.35,
    )
    assert r.valor_lance == 0.0
    assert r.meses_antecipados == 0


def test_calcular_cet_otimista_converge_e_e_positivo():
    consorcio = calcular_consorcio(60000, 60, 17, 2, 0.04, reajuste_anual=0.0, seguro_sobre_saldo=False)
    cet = calcular_cet(consorcio.parcelas, 60000, mes_contemplacao=1)
    assert cet.convergiu
    assert cet.cet_anual is not None
    assert cet.cet_anual > 0, "CET otimista (contemplacao imediata) deve ser positivo, ha custo real"


def test_calcular_cet_conservador_pode_ser_negativo():
    consorcio = calcular_consorcio(60000, 60, 17, 2, 0.04, reajuste_anual=0.0, seguro_sobre_saldo=False)
    cet = calcular_cet(consorcio.parcelas, 60000, mes_contemplacao=60)
    assert cet.convergiu
    assert cet.cet_anual is not None
    assert cet.cet_anual < 0, "contemplacao so no ultimo mes tende a um CET negativo (poupanca com desagio)"


def test_calcular_cet_mes_intermediario_pode_nao_convergir():
    """Propriedade conhecida: para meses intermediarios pode nao existir TIR real."""
    consorcio = calcular_consorcio(60000, 60, 17, 2, 0.04, reajuste_anual=0.0, seguro_sobre_saldo=False)
    cet = calcular_cet(consorcio.parcelas, 60000, mes_contemplacao=30)
    assert cet.convergiu is False
    assert cet.cet_mensal is None
    assert cet.cet_anual is None


def test_calcular_cet_mes_fora_do_intervalo_nao_quebra():
    consorcio = calcular_consorcio(60000, 60, 17, 2, 0.04)
    cet = calcular_cet(consorcio.parcelas, 60000, mes_contemplacao=999)
    assert cet.convergiu is False


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
