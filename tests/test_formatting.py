"""Testes unitários dos helpers de formatação."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.formatting import cor_card, fmt_brl, fmt_brl_full, fmt_meses, fmt_pct, fmt_pct_precisa


def test_fmt_brl_faixas():
    assert fmt_brl(500) == "R$ 500"
    assert fmt_brl(1500) == "R$ 1.5k"
    assert fmt_brl(1_500_000) == "R$ 1.50M"
    assert fmt_brl(-2000) == "-R$ 2.0k"


def test_fmt_brl_full():
    assert fmt_brl_full(1234.5) == "R$ 1.234,50"
    assert fmt_brl_full(-500) == "-R$ 500,00"


def test_fmt_pct():
    assert fmt_pct(12.345) == "12.3%"
    assert fmt_pct(-5.0) == "-5.0%"


def test_fmt_pct_precisa():
    assert fmt_pct_precisa(8.512) == "8.51%"
    assert fmt_pct_precisa(-7.851) == "-7.85%"


def test_fmt_meses():
    assert fmt_meses(None) == "fora do prazo"
    assert fmt_meses(5) == "5m"
    assert fmt_meses(12) == "1a"
    assert fmt_meses(14) == "1a 2m"


def test_cor_card():
    assert cor_card(10) == "metric-value"
    assert cor_card(-10) == "metric-value danger"
    assert cor_card(0) == "metric-value"
