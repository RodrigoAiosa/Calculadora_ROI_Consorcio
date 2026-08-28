"""
Comparador de administradoras de consórcio via importação de CSV.

Lê um CSV com propostas de diferentes administradoras e rankeia por CET
(Custo Efetivo Total), usando o mesmo motor de cálculo do restante da
ferramenta (`calcular_consorcio` + `calcular_cet`).
"""

import io
from dataclasses import dataclass

import pandas as pd

from src.calculations import calcular_cet, calcular_consorcio

COLUNAS_OBRIGATORIAS = [
    "administradora", "valor_credito", "prazo_meses",
    "taxa_adm", "fundo_reserva", "seguro_perc",
]


@dataclass
class LinhaComparador:
    administradora: str
    valor_credito: float
    prazo_meses: int
    parcela_media: float
    custo_total: float
    cet_anual: float | None
    erro: str | None = None


class ComparadorCSVError(ValueError):
    """Erro de validação do CSV de administradoras."""


def gerar_csv_exemplo() -> str:
    """Retorna um CSV de exemplo (string) com o formato esperado pelo comparador."""
    df = pd.DataFrame([
        {"administradora": "Administradora A", "valor_credito": 60000, "prazo_meses": 60,
         "taxa_adm": 17.0, "fundo_reserva": 2.0, "seguro_perc": 0.04},
        {"administradora": "Administradora B", "valor_credito": 60000, "prazo_meses": 60,
         "taxa_adm": 14.5, "fundo_reserva": 1.5, "seguro_perc": 0.05},
        {"administradora": "Administradora C", "valor_credito": 60000, "prazo_meses": 72,
         "taxa_adm": 19.0, "fundo_reserva": 2.0, "seguro_perc": 0.03},
    ])
    return str(df.to_csv(index=False))


def validar_csv(df: pd.DataFrame) -> None:
    faltantes = [c for c in COLUNAS_OBRIGATORIAS if c not in df.columns]
    if faltantes:
        raise ComparadorCSVError(
            f"Colunas obrigatórias ausentes no CSV: {', '.join(faltantes)}. "
            f"Colunas esperadas: {', '.join(COLUNAS_OBRIGATORIAS)}."
        )
    if df.empty:
        raise ComparadorCSVError("O CSV enviado está vazio.")


def comparar_administradoras(
    csv_bytes: bytes,
    mes_contemplacao_cet: str = "otimista",
) -> list[LinhaComparador]:
    """
    Processa o CSV de propostas e retorna uma lista de `LinhaComparador`
    ordenada por CET anual crescente (menor custo primeiro). Linhas com erro
    de cálculo aparecem por último, com `erro` preenchido.

    `mes_contemplacao_cet`: "otimista" (mês 1) ou "conservador" (último mês).
    """
    df = pd.read_csv(io.BytesIO(csv_bytes))
    validar_csv(df)

    resultados: list[LinhaComparador] = []
    for _, row in df.iterrows():
        try:
            valor_credito = float(row["valor_credito"])
            prazo_meses = int(row["prazo_meses"])
            taxa_adm = float(row["taxa_adm"])
            fundo_reserva = float(row["fundo_reserva"])
            seguro_perc = float(row["seguro_perc"])
            administradora = str(row["administradora"])

            consorcio = calcular_consorcio(
                valor_credito, prazo_meses, taxa_adm, fundo_reserva, seguro_perc,
                reajuste_anual=0.0, seguro_sobre_saldo=False,
            )
            mes_cet = 1 if mes_contemplacao_cet == "otimista" else prazo_meses
            cet = calcular_cet(consorcio.parcelas, valor_credito, mes_contemplacao=mes_cet)

            resultados.append(LinhaComparador(
                administradora=administradora,
                valor_credito=valor_credito,
                prazo_meses=prazo_meses,
                parcela_media=consorcio.parcela_media,
                custo_total=consorcio.custo_total,
                cet_anual=cet.cet_anual if cet.convergiu else None,
            ))
        except (KeyError, ValueError, TypeError) as e:
            resultados.append(LinhaComparador(
                administradora=str(row.get("administradora", "linha inválida")),
                valor_credito=0.0, prazo_meses=0, parcela_media=0.0, custo_total=0.0,
                cet_anual=None, erro=str(e),
            ))

    resultados.sort(key=lambda r: (r.cet_anual is None, r.cet_anual if r.cet_anual is not None else float("inf")))
    return resultados
