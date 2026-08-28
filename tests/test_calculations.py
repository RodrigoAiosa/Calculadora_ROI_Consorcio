"""Testes unitários dos cálculos financeiros (sem dependência do Streamlit)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.calculations import calcular_consorcio, calcular_financiamento, calcular_investimento, calcular_lance


def test_calcular_consorcio_basico():
    r = calcular_consorcio(valor_credito=60000, prazo_meses=60, taxa_adm=17, fundo_reserva=2, seguro_perc=0.04)
    assert round(r.parcela, 2) == 1214.0
    assert round(r.custo_total, 2) == 72840.0


def test_calcular_financiamento_price():
    consorcio = calcular_consorcio(60000, 60, 17, 2, 0.04)
    r = calcular_financiamento(
        valor_credito=60000, taxa_financiamento=1.7, prazo_meses=60,
        custo_total_consorcio=consorcio.custo_total,
    )
    assert round(r.parcela, 2) == 1603.02
    # o financiamento deve custar mais que o consórcio nesse cenário
    assert r.economia_consorcio > 0


def test_calcular_financiamento_taxa_zero():
    r = calcular_financiamento(valor_credito=12000, taxa_financiamento=0, prazo_meses=12, custo_total_consorcio=12000)
    assert round(r.parcela, 2) == 1000.0


def test_calcular_investimento_encontra_cruzamento():
    consorcio = calcular_consorcio(60000, 60, 17, 2, 0.04)
    r = calcular_investimento(
        parcela_consorcio=consorcio.parcela, valor_credito=60000,
        taxa_investimento=0.85, correcao_bem=0.35, prazo_meses=60,
    )
    assert r.mes_cruzamento is not None
    assert r.mes_cruzamento <= 60
    # no mês do cruzamento, o valor investido já alcançou o valor do bem
    assert r.serie_investido[r.mes_cruzamento] >= r.serie_bem_corrigido[r.mes_cruzamento]


def test_calcular_investimento_sem_cruzamento_quando_correcao_alta():
    consorcio = calcular_consorcio(60000, 60, 17, 2, 0.04)
    r = calcular_investimento(
        parcela_consorcio=consorcio.parcela, valor_credito=60000,
        taxa_investimento=0.1, correcao_bem=5.0, prazo_meses=60,
    )
    assert r.mes_cruzamento is None
    assert r.ganho_final < 0


def test_calcular_lance_reduz_prazo():
    consorcio = calcular_consorcio(60000, 60, 17, 2, 0.04)
    r = calcular_lance(
        parcela_consorcio=consorcio.parcela, valor_credito=60000,
        perc_lance=25, mes_lance=12, prazo_meses=60,
        taxa_investimento=0.85, correcao_bem=0.35,
    )
    assert r.prazo_final_com_lance < 60
    assert r.meses_antecipados > 0
    assert r.valor_lance == 15000.0


def test_calcular_lance_quita_tudo():
    """Lance muito alto deve contemplar imediatamente (sem parcelas restantes)."""
    consorcio = calcular_consorcio(60000, 60, 17, 2, 0.04)
    r = calcular_lance(
        parcela_consorcio=consorcio.parcela, valor_credito=60000,
        perc_lance=100, mes_lance=12, prazo_meses=60,
        taxa_investimento=0.85, correcao_bem=0.35,
    )
    assert r.prazo_final_com_lance == 12
    assert r.meses_antecipados == 48


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
