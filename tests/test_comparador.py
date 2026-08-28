"""Testes unitários do comparador de administradoras via CSV."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.comparador import ComparadorCSVError, comparar_administradoras, gerar_csv_exemplo


def test_gerar_csv_exemplo_tem_colunas_esperadas():
    csv_str = gerar_csv_exemplo()
    primeira_linha = csv_str.splitlines()[0]
    for coluna in ["administradora", "valor_credito", "prazo_meses", "taxa_adm", "fundo_reserva", "seguro_perc"]:
        assert coluna in primeira_linha


def test_comparar_administradoras_rankeia_por_cet_crescente():
    csv_bytes = gerar_csv_exemplo().encode("utf-8")
    resultados = comparar_administradoras(csv_bytes, mes_contemplacao_cet="otimista")
    assert len(resultados) == 3
    cets = [r.cet_anual for r in resultados if r.cet_anual is not None]
    assert cets == sorted(cets), "resultados deveriam estar ordenados por CET crescente"


def test_comparar_administradoras_csv_sem_colunas_obrigatorias():
    csv_invalido = b"nome,valor\nA,1000\n"
    with pytest.raises(ComparadorCSVError):
        comparar_administradoras(csv_invalido)


def test_comparar_administradoras_csv_vazio():
    csv_vazio = b"administradora,valor_credito,prazo_meses,taxa_adm,fundo_reserva,seguro_perc\n"
    with pytest.raises(ComparadorCSVError):
        comparar_administradoras(csv_vazio)


def test_comparar_administradoras_linha_invalida_nao_quebra_o_resto():
    csv_misto = (
        b"administradora,valor_credito,prazo_meses,taxa_adm,fundo_reserva,seguro_perc\n"
        b"Boa,60000,60,17.0,2.0,0.04\n"
        b"Ruim,abc,60,17.0,2.0,0.04\n"
    )
    resultados = comparar_administradoras(csv_misto)
    assert len(resultados) == 2
    com_erro = [r for r in resultados if r.erro is not None]
    assert len(com_erro) == 1
    assert com_erro[0].administradora == "Ruim"
