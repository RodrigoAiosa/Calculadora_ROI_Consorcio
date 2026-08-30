"""Testes unitários da verificação de senha da tela de acesso."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.auth import senha_valida


def test_senha_valida_aceita_senha_correta():
    assert senha_valida("abc123", "abc123") is True


def test_senha_valida_rejeita_senha_incorreta():
    assert senha_valida("errada", "abc123") is False


def test_senha_valida_rejeita_quando_esperada_vazia():
    assert senha_valida("", "") is False
    assert senha_valida("qualquer", "") is False
