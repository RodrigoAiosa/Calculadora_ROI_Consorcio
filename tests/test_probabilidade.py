"""Testes unitários do simulador de probabilidade de contemplação por sorteio."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.probabilidade import calcular_probabilidade_contemplacao


def test_probabilidade_mes_1_e_1_sobre_n_cotas():
    r = calcular_probabilidade_contemplacao(num_cotas_grupo=200, prazo_meses=60)
    assert abs(r.prob_mensal[0] - 1 / 200) < 1e-9


def test_probabilidade_acumulada_e_monotonica_crescente():
    r = calcular_probabilidade_contemplacao(num_cotas_grupo=200, prazo_meses=60)
    for a, b in zip(r.prob_acumulada, r.prob_acumulada[1:]):
        assert b >= a


def test_probabilidade_acumulada_sem_saidas_extras_e_n_sobre_total():
    """Sem lances/saidas, apos m meses a prob acumulada = m / num_cotas (1 sorteio/mes)."""
    r = calcular_probabilidade_contemplacao(num_cotas_grupo=200, prazo_meses=60)
    assert abs(r.prob_acumulada[-1] - 60 / 200) < 1e-9


def test_probabilidade_cotas_zero_nao_quebra():
    r = calcular_probabilidade_contemplacao(num_cotas_grupo=0, prazo_meses=60)
    assert r.meses == []
    assert r.mes_50_perc is None


def test_probabilidade_multiplas_cotas_por_mes_acelera_contemplacao():
    r1 = calcular_probabilidade_contemplacao(num_cotas_grupo=200, prazo_meses=60, cotas_sorteadas_por_mes=1)
    r2 = calcular_probabilidade_contemplacao(num_cotas_grupo=200, prazo_meses=60, cotas_sorteadas_por_mes=3)
    assert r2.prob_acumulada[-1] > r1.prob_acumulada[-1]
