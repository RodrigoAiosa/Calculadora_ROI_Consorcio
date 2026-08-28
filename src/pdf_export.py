"""Geração de proposta resumida em PDF (1 página) usando reportlab."""

import io
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.calculations import ResultadoCET, ResultadoConsorcio, ResultadoFinanciamento, ResultadoInvestimento, ResultadoLance

_VERDE = colors.HexColor("#166534")
_VERDE_CLARO = colors.HexColor("#DCFCE7")
_CINZA = colors.HexColor("#4B5563")
_CINZA_CLARO = colors.HexColor("#F3F4F6")


_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U00002700-\U000027BF"
    "\U0000FE0F"
    "]+",
    flags=re.UNICODE,
)


def _remover_emoji(texto: str) -> str:
    """Remove emojis do texto — as fontes padrão do reportlab não têm esses glifos
    e renderizam caixas pretas em vez do caractere (ver skill de PDF)."""
    return _EMOJI_RE.sub("", texto).strip()


def _fmt_brl(v: float) -> str:
    s, a = ("-" if v < 0 else ""), abs(v)
    return f"{s}R$ {a:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def gerar_pdf_proposta(
    *,
    cenario_sel: str,
    valor_credito: float,
    prazo_meses: int,
    consorcio: ResultadoConsorcio,
    financiamento: ResultadoFinanciamento,
    investimento: ResultadoInvestimento,
    lance: ResultadoLance,
    cet: ResultadoCET,
) -> io.BytesIO:
    """Gera um PDF de 1 página resumindo os principais números das 4 comparações."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
    )
    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle("TituloConsorcio", parent=styles["Title"], textColor=_VERDE, fontSize=18)
    subtitulo_style = ParagraphStyle("SubtituloConsorcio", parent=styles["Normal"], textColor=_CINZA, fontSize=10, spaceAfter=12)
    secao_style = ParagraphStyle("SecaoConsorcio", parent=styles["Heading2"], textColor=_VERDE, fontSize=12, spaceBefore=14, spaceAfter=6)
    nota_style = ParagraphStyle("NotaConsorcio", parent=styles["Normal"], textColor=_CINZA, fontSize=8, spaceBefore=10)

    story = [
        Paragraph("Proposta — Calculadora de ROI de Consórcio", titulo_style),
        Paragraph(f"Cenário: {_remover_emoji(cenario_sel)} &nbsp;|&nbsp; Crédito: {_fmt_brl(valor_credito)} &nbsp;|&nbsp; Prazo: {prazo_meses} meses", subtitulo_style),
    ]

    def tabela(dados: list[list[str]]) -> Table:
        t = Table(dados, colWidths=[8 * cm, 8 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _VERDE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _CINZA_CLARO]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        return t

    story.append(Paragraph("1. Consórcio x Financiamento", secao_style))
    story.append(tabela([
        ["Métrica", "Valor"],
        ["Parcela do consórcio", _fmt_brl(consorcio.parcela_inicial)],
        ["Parcela do financiamento", _fmt_brl(financiamento.parcela)],
        ["Custo total — consórcio", _fmt_brl(consorcio.custo_total)],
        ["Custo total — financiamento", _fmt_brl(financiamento.custo_total)],
        ["Economia do consórcio", _fmt_brl(financiamento.economia_consorcio)],
    ]))

    story.append(Paragraph("2. Investir e Comprar à Vista", secao_style))
    story.append(tabela([
        ["Métrica", "Valor"],
        [f"Valor do bem corrigido em {prazo_meses}m", _fmt_brl(investimento.serie_bem_corrigido[-1])],
        [f"Valor acumulado investindo em {prazo_meses}m", _fmt_brl(investimento.serie_investido[-1])],
        ["Ganho líquido investindo", _fmt_brl(investimento.ganho_final)],
        ["Mês em que dá para comprar à vista",
         str(investimento.mes_cruzamento) if investimento.mes_cruzamento else "Fora do prazo"],
    ]))

    story.append(Paragraph("3. Lance / Contemplação Antecipada", secao_style))
    story.append(tabela([
        ["Métrica", "Valor"],
        ["Tipo de lance", "Próprio" if lance.tipo == "proprio" else "Embutido"],
        ["Valor do lance", _fmt_brl(lance.valor_lance)],
        ["Meses antecipados", str(lance.meses_antecipados)],
        ["Ganho líquido com o lance", _fmt_brl(lance.ganho_liquido)],
    ]))

    story.append(Paragraph("4. CET — Custo Efetivo Total", secao_style))
    if cet.convergiu and cet.cet_anual is not None:
        cet_linha = f"{cet.cet_anual:+.2f}% ao ano (mês de contemplação considerado: {cet.mes_contemplacao})"
    else:
        cet_linha = "Não foi possível calcular para o mês de contemplação escolhido"
    story.append(tabela([
        ["Métrica", "Valor"],
        ["CET anualizado", cet_linha],
    ]))

    story.append(Paragraph(
        "⚠️ Ferramenta educacional. Taxas de administração, seguro, juros de financiamento, "
        "rendimento de investimento, reajuste anual e correção do bem são estimativas informadas "
        "pelo usuário. Confira sempre as condições reais junto à administradora de consórcio, ao "
        "banco e ao mercado antes de decidir. Este documento não substitui uma simulação oficial "
        "nem consultoria financeira.",
        nota_style,
    ))

    doc.build(story)
    buf.seek(0)
    return buf
