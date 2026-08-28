"""
Calculadora de ROI de Consórcio
===============================

Ferramenta educacional em Streamlit que compara consórcio, financiamento,
investir e comprar à vista, e antecipação por lance — para ajudar a decidir
se um consórcio (veículo, imóvel, máquina etc.) vale a pena no seu cenário.

Execução:
    pip install -r requirements.txt
    streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.calculations import calcular_consorcio, calcular_financiamento, calcular_investimento, calcular_lance
from src.excel_export import gerar_excel
from src.formatting import cor_card, fmt_brl, fmt_meses, fmt_pct
from src.scenarios import CENARIOS

BASE_DIR = Path(__file__).parent


# ─────────────────────────────────────────────────────────────────────────────
# Configuração da página e estilo
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ROI de Consórcio",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)


def carregar_css(caminho: Path) -> None:
    with open(caminho, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


carregar_css(BASE_DIR / "assets" / "style.css")


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — cenário e parâmetros de entrada
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="header-tag">// Cenários</div>', unsafe_allow_html=True)
    st.markdown("## Configuração")
    st.markdown("Selecione um cenário ou configure manualmente.")
    st.markdown("---")

    cenario_sel = st.selectbox("📋 Cenário", list(CENARIOS.keys()))
    dados = CENARIOS[cenario_sel]

    def d(campo: str, default: float):
        return float(dados[campo]) if dados else default

    st.markdown('<div class="section-title">Dados do Consórcio</div>', unsafe_allow_html=True)
    valor_credito = st.number_input("Valor da carta de crédito (R$)", min_value=1000.0, value=d("valor_credito", 60000.0), step=1000.0)
    prazo_meses = st.slider("Prazo do grupo (meses)", 12, 240, value=int(dados["prazo_meses"]) if dados else 60, step=1)
    taxa_adm = st.number_input("Taxa de administração total (%)", min_value=0.0, value=d("taxa_adm", 17.0), step=0.5)
    fundo_reserva = st.number_input("Fundo de reserva (%)", min_value=0.0, value=d("fundo_reserva", 2.0), step=0.5)
    seguro_perc = st.number_input("Seguro mensal (% do crédito/mês)", min_value=0.0, value=d("seguro_perc", 0.04), step=0.01, format="%.3f")

    st.markdown('<div class="section-title">Lance (contemplação antecipada)</div>', unsafe_allow_html=True)
    perc_lance = st.number_input("Lance ofertado (% do crédito)", min_value=0.0, max_value=100.0, value=d("perc_lance", 25.0), step=1.0)
    mes_lance = st.slider("Mês em que o lance seria ofertado", 1, prazo_meses, value=min(int(dados["mes_lance"]) if dados else 12, prazo_meses))

    st.markdown('<div class="section-title">Comparação: Financiamento</div>', unsafe_allow_html=True)
    taxa_financiamento = st.number_input("Juros do financiamento (% a.m.)", min_value=0.0, value=d("taxa_financiamento", 1.7), step=0.1)

    st.markdown('<div class="section-title">Comparação: Investir e comprar à vista</div>', unsafe_allow_html=True)
    taxa_investimento = st.number_input("Rendimento do investimento (% a.m.)", min_value=0.0, value=d("taxa_investimento", 0.85), step=0.05)
    correcao_bem = st.number_input("Valorização/correção do bem (% a.m.)", min_value=0.0, value=d("correcao_bem", 0.35), step=0.05)

    st.markdown("---")


# ─────────────────────────────────────────────────────────────────────────────
# Cálculos
# ─────────────────────────────────────────────────────────────────────────────
consorcio = calcular_consorcio(valor_credito, prazo_meses, taxa_adm, fundo_reserva, seguro_perc)
financiamento = calcular_financiamento(valor_credito, taxa_financiamento, prazo_meses, consorcio.custo_total)
investimento = calcular_investimento(consorcio.parcela, valor_credito, taxa_investimento, correcao_bem, prazo_meses)
lance = calcular_lance(consorcio.parcela, valor_credito, perc_lance, mes_lance, prazo_meses, taxa_investimento, correcao_bem)

meses_eixo = investimento.meses


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — exportação
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-title">Exportar</div>', unsafe_allow_html=True)
    excel_buf = gerar_excel(
        cenario_sel=cenario_sel,
        valor_credito=valor_credito,
        prazo_meses=prazo_meses,
        taxa_adm=taxa_adm,
        fundo_reserva=fundo_reserva,
        seguro_perc=seguro_perc,
        perc_lance=perc_lance,
        mes_lance=mes_lance,
        taxa_financiamento=taxa_financiamento,
        taxa_investimento=taxa_investimento,
        correcao_bem=correcao_bem,
        parcela_consorcio=consorcio.parcela,
        custo_total_consorcio=consorcio.custo_total,
        financiamento=financiamento,
        investimento=investimento,
        lance=lance,
    )
    nome_arquivo = cenario_sel
    for e in ["🎯", "🚗", "🚙", "🏍️", "🏠", "🏢", "🚚", " ", "/"]:
        nome_arquivo = nome_arquivo.replace(e, "_")
    nome_arquivo = nome_arquivo.strip("_")
    st.download_button(
        label="📥 Exportar para Excel",
        data=excel_buf,
        file_name=f"roi_consorcio_{nome_arquivo}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="header-tag">// Calculadora</div>', unsafe_allow_html=True)
st.title("Calculadora ROI de Consórcio")
if cenario_sel != "🎯 Personalizado":
    st.markdown(f'<span class="scenario-badge">{cenario_sel}</span>', unsafe_allow_html=True)
st.caption("Compare consórcio, financiamento, investir à vista e antecipação por lance — em um só lugar.")
st.markdown("---")


# ─────────────────────────────────────────────────────────────────────────────
# Resumo geral
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Resumo Geral</div>', unsafe_allow_html=True)

melhor_opcao = "Consórcio"
if financiamento.economia_consorcio < 0:
    melhor_opcao = "Financiamento"
if investimento.ganho_final > max(financiamento.economia_consorcio, 0):
    melhor_opcao = "Investir e comprar à vista"

st.markdown(f"""
<div class="metrics-row">
  <div class="metric-card">
    <div class="metric-label">Parcela Consórcio</div>
    <div class="metric-value info">{fmt_brl(consorcio.parcela)}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Custo Total Consórcio</div>
    <div class="metric-value warning">{fmt_brl(consorcio.custo_total)}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Economia vs. Financiamento</div>
    <div class="{cor_card(financiamento.economia_consorcio)}">{fmt_brl(financiamento.economia_consorcio)}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Melhor Opção</div>
    <div class="metric-value">{melhor_opcao}</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="disclaimer-box">
<p>⚠️ Ferramenta educacional. Taxas de administração, seguro, juros de financiamento, rendimento de investimento e
valorização do bem são estimativas informadas por você. Confira sempre as condições reais junto à administradora
de consórcio, ao banco e ao mercado antes de decidir.</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Layout comum dos gráficos Plotly
# ─────────────────────────────────────────────────────────────────────────────
def aplicar_layout(fig: go.Figure) -> None:
    fig.update_layout(
        paper_bgcolor="#0a0a0f", plot_bgcolor="#0f0f1a",
        font=dict(family="Space Mono, monospace", color="#9ca3af", size=11),
        legend=dict(bgcolor="rgba(26,26,46,0.9)", bordercolor="#2d2d4e", borderwidth=1, font=dict(size=11)),
        xaxis=dict(title="Meses", gridcolor="#1e1e2e", zerolinecolor="#2d2d4e"),
        yaxis=dict(title="R$", gridcolor="#1e1e2e", zerolinecolor="#2d2d4e", tickprefix="R$ ", tickformat=",.0f"),
        hovermode="x unified", margin=dict(l=10, r=10, t=20, b=10), height=380,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["💳 Consórcio x Financiamento", "📈 Investir e Comprar à Vista", "🎯 Lance / Contemplação"])

# ── TAB 1: Financiamento ─────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-title">Resultados</div>', unsafe_allow_html=True)
    pay_cor = cor_card(financiamento.economia_consorcio)
    st.markdown(f"""
    <div class="metrics-row">
      <div class="metric-card">
        <div class="metric-label">Parcela Financiamento</div>
        <div class="metric-value warning">{fmt_brl(financiamento.parcela)}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Custo Total Financiamento</div>
        <div class="metric-value danger">{fmt_brl(financiamento.custo_total)}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Economia do Consórcio</div>
        <div class="{pay_cor}">{fmt_brl(financiamento.economia_consorcio)}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Economia (%)</div>
        <div class="{pay_cor}">{fmt_pct(financiamento.economia_consorcio_perc)}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=meses_eixo, y=[consorcio.parcela * m for m in meses_eixo],
                               name="Custo acumulado — Consórcio", line=dict(color="#4ade80", width=2.5)))
    fig1.add_trace(go.Scatter(x=meses_eixo, y=[financiamento.parcela * m for m in meses_eixo],
                               name="Custo acumulado — Financiamento", line=dict(color="#f87171", width=2.5, dash="dash")))
    aplicar_layout(fig1)
    st.plotly_chart(fig1, use_container_width=True)

    with st.expander("📋 Ver tabela mês a mês"):
        df1 = pd.DataFrame({
            "Mês": meses_eixo,
            "Custo Acumulado Consórcio": [f"R$ {consorcio.parcela*m:,.2f}" for m in meses_eixo],
            "Custo Acumulado Financiamento": [f"R$ {financiamento.parcela*m:,.2f}" for m in meses_eixo],
            "Diferença": [f"R$ {(financiamento.parcela-consorcio.parcela)*m:,.2f}" for m in meses_eixo],
        })
        st.dataframe(df1, use_container_width=True, hide_index=True)

    st.markdown(f"""
    <div class="summary-box">
    <p>
    Ao final de <strong>{prazo_meses} meses</strong>, o consórcio custa <strong>{fmt_brl(consorcio.custo_total)}</strong> contra
    <strong>{fmt_brl(financiamento.custo_total)}</strong> do financiamento (mesma taxa/mesmo prazo comparativo).
    {"O consórcio é <strong>"+fmt_brl(financiamento.economia_consorcio)+"</strong> mais barato ("+fmt_pct(financiamento.economia_consorcio_perc)+" de economia)." if financiamento.economia_consorcio >= 0 else "Nesse cenário o financiamento sai <strong>"+fmt_brl(abs(financiamento.economia_consorcio))+"</strong> mais barato — a taxa de administração do consórcio está pesando mais que os juros do financiamento."}
    </p>
    </div>
    """, unsafe_allow_html=True)

# ── TAB 2: Investir e comprar à vista ────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-title">Resultados</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="metrics-row">
      <div class="metric-card">
        <div class="metric-label">Bem Corrigido em {prazo_meses}m</div>
        <div class="metric-value warning">{fmt_brl(investimento.serie_bem_corrigido[-1])}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Acumulado Investindo em {prazo_meses}m</div>
        <div class="metric-value info">{fmt_brl(investimento.serie_investido[-1])}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Ganho Líquido Investindo</div>
        <div class="{cor_card(investimento.ganho_final)}">{fmt_brl(investimento.ganho_final)}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Mês p/ Comprar à Vista</div>
        <div class="metric-value">{fmt_meses(investimento.mes_cruzamento) if investimento.mes_cruzamento else "Fora do prazo"}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=meses_eixo, y=investimento.serie_investido, name="Valor acumulado investindo",
                               line=dict(color="#60a5fa", width=2.5)))
    fig2.add_trace(go.Scatter(x=meses_eixo, y=investimento.serie_bem_corrigido, name="Valor do bem corrigido",
                               line=dict(color="#fb923c", width=2.5, dash="dash")))
    if investimento.mes_cruzamento is not None:
        fig2.add_vline(x=investimento.mes_cruzamento, line_dash="dot", line_color="#4ade80", line_width=1.5,
                        annotation_text=f"Cruzamento: mês {investimento.mes_cruzamento}",
                        annotation_font_color="#4ade80", annotation_position="top right")
    aplicar_layout(fig2)
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("📋 Ver tabela mês a mês"):
        df2 = pd.DataFrame({
            "Mês": meses_eixo,
            "Valor Investido Acumulado": [f"R$ {v:,.2f}" for v in investimento.serie_investido],
            "Valor do Bem Corrigido": [f"R$ {v:,.2f}" for v in investimento.serie_bem_corrigido],
            "Diferença": [f"R$ {(a-b):,.2f}" for a, b in zip(investimento.serie_investido, investimento.serie_bem_corrigido)],
        })
        st.dataframe(df2, use_container_width=True, hide_index=True)

    texto_cruzamento = (
        f"Investindo a parcela mensal em vez de entrar no consórcio, você acumularia o suficiente para comprar o bem à vista por volta do <strong>mês {investimento.mes_cruzamento}</strong>."
        if investimento.mes_cruzamento is not None else
        f"Dentro do prazo de {prazo_meses} meses, o valor investido <strong>não alcança</strong> o valor do bem corrigido — o bem se valoriza mais rápido do que o dinheiro rende nesse cenário."
    )
    st.markdown(f"""
    <div class="summary-box">
    <p>
    {texto_cruzamento}
    <br><br>
    Ao final do prazo, a diferença entre investir e comprar à vista versus entrar no consórcio é de
    <strong>{fmt_brl(investimento.ganho_final)}</strong>
    {"a favor de investir." if investimento.ganho_final >= 0 else "a favor do consórcio (a valorização do bem supera o rendimento do investimento)."}
    </p>
    </div>
    """, unsafe_allow_html=True)

# ── TAB 3: Lance ──────────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-title">Resultados</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="metrics-row">
      <div class="metric-card">
        <div class="metric-label">Valor do Lance</div>
        <div class="metric-value warning">{fmt_brl(lance.valor_lance)}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Meses Antecipados</div>
        <div class="metric-value info">{lance.meses_antecipados}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Benefício da Antecipação</div>
        <div class="metric-value">{fmt_brl(lance.beneficio_valorizacao_evitada)}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Ganho Líquido do Lance</div>
        <div class="{cor_card(lance.ganho_liquido)}">{fmt_brl(lance.ganho_liquido)}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=meses_eixo, y=lance.serie_saldo_sem_lance, name="Saldo devedor — sem lance",
                               line=dict(color="#f87171", width=2.5, dash="dash")))
    fig3.add_trace(go.Scatter(x=meses_eixo, y=lance.serie_saldo_com_lance, name="Saldo devedor — com lance",
                               line=dict(color="#4ade80", width=2.5), fill="tozeroy", fillcolor="rgba(74,222,128,0.08)"))
    fig3.add_vline(x=mes_lance, line_dash="dot", line_color="#fb923c", line_width=1.5,
                    annotation_text=f"Lance: mês {mes_lance}",
                    annotation_font_color="#fb923c", annotation_position="top right")
    aplicar_layout(fig3)
    st.plotly_chart(fig3, use_container_width=True)

    with st.expander("📋 Ver tabela mês a mês"):
        df3 = pd.DataFrame({
            "Mês": meses_eixo,
            "Saldo Devedor sem Lance": [f"R$ {v:,.2f}" for v in lance.serie_saldo_sem_lance],
            "Saldo Devedor com Lance": [f"R$ {v:,.2f}" for v in lance.serie_saldo_com_lance],
        })
        st.dataframe(df3, use_container_width=True, hide_index=True)

    st.markdown(f"""
    <div class="summary-box">
    <p>
    Ofertando um lance de <strong>{fmt_brl(lance.valor_lance)}</strong> no mês {mes_lance}, a contemplação sai do mês {prazo_meses}
    para o mês <strong>{lance.prazo_final_com_lance}</strong> — uma antecipação de <strong>{lance.meses_antecipados} meses</strong>.
    Isso evita <strong>{fmt_brl(lance.beneficio_valorizacao_evitada)}</strong> em valorização do bem, mas abre mão de
    <strong>{fmt_brl(lance.custo_oportunidade_lance)}</strong> que esse dinheiro renderia se ficasse investido.
    Ganho líquido estimado: <strong>{fmt_brl(lance.ganho_liquido)}</strong>
    {"— vale a pena antecipar." if lance.ganho_liquido >= 0 else "— nesse cenário, pode compensar mais manter o dinheiro investido e não ofertar lance."}
    </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.caption("Calculadora educacional de ROI de Consórcio.")
