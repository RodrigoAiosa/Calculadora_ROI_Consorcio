"""
Cenários pré-definidos para a Calculadora de ROI de Consórcio.

Os valores são ilustrativos/educacionais (taxas de administração, seguro,
juros de financiamento, rendimento de investimento, reajuste anual e
correção do bem variam bastante entre administradoras, bancos e período).
Ajuste com os dados reais da sua simulação antes de tomar qualquer decisão
financeira.
"""

from typing import Optional, TypedDict


class Cenario(TypedDict):
    valor_credito: float
    prazo_meses: int
    taxa_adm: float
    fundo_reserva: float
    seguro_perc: float
    taxa_financiamento: float
    taxa_investimento: float
    correcao_bem: float
    reajuste_anual: float
    num_cotas_grupo: int
    perc_lance: float
    mes_lance: int
    tipo_lance: str


CENARIOS: dict[str, Optional[Cenario]] = {
    "🎯 Personalizado": None,
    "🚗 Carro Popular": {
        "valor_credito": 60000.0, "prazo_meses": 60, "taxa_adm": 17.0, "fundo_reserva": 2.0,
        "seguro_perc": 0.04, "taxa_financiamento": 1.7, "taxa_investimento": 0.85,
        "correcao_bem": 0.35, "reajuste_anual": 4.5, "num_cotas_grupo": 200,
        "perc_lance": 25.0, "mes_lance": 12, "tipo_lance": "proprio",
    },
    "🚙 Carro Premium / SUV": {
        "valor_credito": 180000.0, "prazo_meses": 72, "taxa_adm": 16.0, "fundo_reserva": 2.0,
        "seguro_perc": 0.03, "taxa_financiamento": 1.6, "taxa_investimento": 0.85,
        "correcao_bem": 0.30, "reajuste_anual": 4.0, "num_cotas_grupo": 150,
        "perc_lance": 30.0, "mes_lance": 18, "tipo_lance": "proprio",
    },
    "🏍️ Moto": {
        "valor_credito": 22000.0, "prazo_meses": 48, "taxa_adm": 15.0, "fundo_reserva": 1.0,
        "seguro_perc": 0.05, "taxa_financiamento": 2.0, "taxa_investimento": 0.85,
        "correcao_bem": 0.40, "reajuste_anual": 5.0, "num_cotas_grupo": 250,
        "perc_lance": 20.0, "mes_lance": 10, "tipo_lance": "proprio",
    },
    "🏠 Apartamento": {
        "valor_credito": 350000.0, "prazo_meses": 180, "taxa_adm": 19.0, "fundo_reserva": 2.0,
        "seguro_perc": 0.02, "taxa_financiamento": 0.90, "taxa_investimento": 0.85,
        "correcao_bem": 0.45, "reajuste_anual": 6.0, "num_cotas_grupo": 300,
        "perc_lance": 25.0, "mes_lance": 24, "tipo_lance": "embutido",
    },
    "🏢 Imóvel Alto Padrão": {
        "valor_credito": 900000.0, "prazo_meses": 200, "taxa_adm": 20.0, "fundo_reserva": 2.0,
        "seguro_perc": 0.015, "taxa_financiamento": 0.85, "taxa_investimento": 0.90,
        "correcao_bem": 0.40, "reajuste_anual": 5.5, "num_cotas_grupo": 180,
        "perc_lance": 30.0, "mes_lance": 30, "tipo_lance": "embutido",
    },
    "🚚 Caminhão / Máquina": {
        "valor_credito": 280000.0, "prazo_meses": 84, "taxa_adm": 14.0, "fundo_reserva": 2.0,
        "seguro_perc": 0.03, "taxa_financiamento": 1.5, "taxa_investimento": 0.85,
        "correcao_bem": 0.35, "reajuste_anual": 4.5, "num_cotas_grupo": 120,
        "perc_lance": 25.0, "mes_lance": 15, "tipo_lance": "proprio",
    },
}
