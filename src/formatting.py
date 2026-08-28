"""Helpers de formatação de números para exibição na interface."""


def fmt_brl(v: float) -> str:
    """Formata valor monetário compacto: R$ 1.2k, R$ 3.40M, -R$ 500."""
    s, a = ("-" if v < 0 else ""), abs(v)
    if a >= 1_000_000:
        return f"{s}R$ {a/1_000_000:.2f}M"
    if a >= 1_000:
        return f"{s}R$ {a/1_000:.1f}k"
    return f"{s}R$ {a:.0f}"


def fmt_brl_full(v: float) -> str:
    """Formata valor monetário por extenso: R$ 1.234,56 (para tabelas/Excel/PDF)."""
    s, a = ("-" if v < 0 else ""), abs(v)
    return f"{s}R$ {a:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(v: float) -> str:
    s, a = ("-" if v < 0 else ""), abs(v)
    return f"{s}{a:.1f}%"


def fmt_pct_precisa(v: float) -> str:
    """Formata percentual com 2 casas decimais (para taxas como CET)."""
    s, a = ("-" if v < 0 else ""), abs(v)
    return f"{s}{a:.2f}%"


def fmt_meses(m: int | None) -> str:
    if m is None:
        return "fora do prazo"
    anos_, meses_ = divmod(int(round(m)), 12)
    if anos_ == 0:
        return f"{meses_}m"
    return f"{anos_}a {meses_}m" if meses_ else f"{anos_}a"


def cor_card(v: float, pos: str = "metric-value", neg: str = "metric-value danger") -> str:
    """Retorna a classe CSS do card conforme o sinal do valor."""
    return pos if v >= 0 else neg
