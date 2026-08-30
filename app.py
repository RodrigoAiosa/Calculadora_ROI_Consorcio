"""
Calculadora de ROI de Consórcio
===============================

Ferramenta educacional em Streamlit que compara consórcio, financiamento,
investir e comprar à vista, e antecipação por lance — além de CET,
probabilidade de contemplação por sorteio e comparação de administradoras
via CSV — para ajudar a decidir se um consórcio vale a pena no seu cenário.

Execução:
    pip install -r requirements.txt
    streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.auth import CHAVE_NOME, CHAVE_SESSAO, exigir_login
from src.calculations import calcular_cet, calcular_consorcio, calcular_financiamento, calcular_investimento, calcular_lance
from src.comparador import ComparadorCSVError, comparar_administradoras, gerar_csv_exemplo
from src.excel_export import gerar_excel
from src.formatting import cor_card, fmt_brl, fmt_meses, fmt_pct, fmt_pct_precisa
from src.glossario import GLOSSARIO
from src.investimento_imovel import calcular_investimento_imovel
from src.pdf_export import gerar_pdf_proposta
from src.probabilidade import calcular_probabilidade_contemplacao
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
exigir_login()


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — cenário e parâmetros de entrada
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    col_saudacao, col_sair = st.columns([3, 1])
    with col_saudacao:
        st.markdown(f'<div class="user-greeting">👋 {st.session_state.get(CHAVE_NOME, "")}</div>', unsafe_allow_html=True)
    with col_sair:
        if st.button("Sair", use_container_width=True):
            st.session_state.pop(CHAVE_SESSAO, None)
            st.session_state.pop(CHAVE_NOME, None)
            st.rerun()
    st.markdown("---")

    st.markdown('<div class="header-tag">// Cenários</div>', unsafe_allow_html=True)
    st.markdown("## Configuração")
    st.markdown("Selecione um cenário ou configure manualmente.")
    st.markdown("---")

    cenario_sel = st.selectbox("📋 Cenário", list(CENARIOS.keys()))
    dados = CENARIOS[cenario_sel]

    def d(campo: str, default):
        return dados[campo] if dados else default

    st.markdown('<div class="section-title">Dados do Consórcio</div>', unsafe_allow_html=True)
    valor_credito = st.number_input(
        "Valor da carta de crédito (R$)", min_value=1000.0, value=float(d("valor_credito", 60000.0)), step=1000.0,
        help="Valor do bem/crédito contratado junto à administradora.",
    )
    prazo_meses = st.slider(
        "Prazo do grupo (meses)", 12, 240, value=int(d("prazo_meses", 60)), step=1,
        help="Duração total do grupo de consórcio, em meses.",
    )
    taxa_adm = st.number_input(
        "Taxa de administração total (%)", min_value=0.0, value=float(d("taxa_adm", 17.0)), step=0.5,
        help="Percentual total (sobre o crédito) cobrado pela administradora ao longo de todo o prazo — a principal receita dela, já que não há juros no consórcio.",
    )
    fundo_reserva = st.number_input(
        "Fundo de reserva (%)", min_value=0.0, value=float(d("fundo_reserva", 2.0)), step=0.5,
        help="Percentual retido para cobrir inadimplência de outros participantes do grupo.",
    )
    seguro_perc = st.number_input(
        "Seguro mensal (% do saldo devedor)", min_value=0.0, value=float(d("seguro_perc", 0.04)), step=0.01, format="%.3f",
        help="Percentual mensal cobrado sobre o saldo devedor remanescente, cobrindo morte/invalidez do participante.",
    )

    st.markdown('<div class="section-title">Reajuste Anual</div>', unsafe_allow_html=True)
    reajuste_anual = st.number_input(
        "Reajuste anual — INCC/IPCA (%)", min_value=0.0, value=float(d("reajuste_anual", 4.5)), step=0.5,
        help="A cada 12 meses (aniversário do grupo), o saldo devedor e o crédito são reajustados por este índice — INCC para imóveis, IPCA para veículos/outros bens. Use 0 para simular sem reajuste.",
    )

    st.markdown('<div class="section-title">Lance (contemplação antecipada)</div>', unsafe_allow_html=True)
    perc_lance = st.number_input(
        "Lance ofertado (% do crédito)", min_value=0.0, max_value=100.0, value=float(d("perc_lance", 25.0)), step=1.0,
        help="Percentual do valor do crédito (atualizado) ofertado como lance para tentar antecipar a contemplação.",
    )
    mes_lance = st.slider(
        "Mês em que o lance seria ofertado", 1, prazo_meses, value=min(int(d("mes_lance", 12)), prazo_meses),
    )
    tipo_lance = st.radio(
        "Tipo de lance", options=["proprio", "embutido"],
        format_func=lambda x: "💰 Próprio (dinheiro extra)" if x == "proprio" else "📉 Embutido (parte do crédito)",
        index=0 if d("tipo_lance", "proprio") == "proprio" else 1, horizontal=False,
        help="Próprio: dinheiro à parte, saído do seu bolso. Embutido: parte do próprio crédito é usada como lance, sem desembolso extra, mas você recebe um crédito líquido menor.",
    )

    st.markdown('<div class="section-title">Comparação: Financiamento</div>', unsafe_allow_html=True)
    taxa_financiamento = st.number_input(
        "Juros do financiamento (% a.m.)", min_value=0.0, value=float(d("taxa_financiamento", 1.7)), step=0.1,
        help="Taxa de juros mensal de um financiamento equivalente (Tabela Price), para comparação.",
    )

    st.markdown('<div class="section-title">Comparação: Investir e comprar à vista</div>', unsafe_allow_html=True)
    taxa_investimento = st.number_input(
        "Rendimento do investimento (% a.m.)", min_value=0.0, value=float(d("taxa_investimento", 0.85)), step=0.05,
        help="Rendimento mensal estimado de uma aplicação financeira (CDB, Tesouro, fundos), para simular investir em vez de entrar no consórcio.",
    )
    correcao_bem = st.number_input(
        "Valorização/correção do bem (% a.m.)", min_value=0.0, value=float(d("correcao_bem", 0.35)), step=0.05,
        help="Estimativa contínua mensal de valorização/inflação do bem, usada para comparar com o rendimento do investimento (independente do reajuste anual discreto do consórcio).",
    )

    st.markdown('<div class="section-title">CET — Mês de Contemplação</div>', unsafe_allow_html=True)
    cenario_cet = st.selectbox(
        "Cenário para cálculo do CET",
        options=["otimista", "conservador", "personalizado"],
        format_func=lambda x: {"otimista": "🟢 Otimista (mês 1)", "conservador": "🔴 Conservador (último mês)", "personalizado": "🎯 Personalizado"}[x],
        help="O CET depende de QUANDO você é contemplado. 'Otimista' assume contemplação imediata (mês 1) — comparável a um financiamento. 'Conservador' assume contemplação só no último mês do grupo — pode até dar uma taxa negativa (nesse caso, o consórcio funcionou como uma poupança com deságio).",
    )
    if cenario_cet == "personalizado":
        mes_contemplacao_cet = st.slider("Mês de contemplação assumido para o CET", 1, prazo_meses, value=max(1, prazo_meses // 2))
    else:
        mes_contemplacao_cet = 1 if cenario_cet == "otimista" else prazo_meses

    st.markdown('<div class="section-title">Probabilidade de Sorteio</div>', unsafe_allow_html=True)
    num_cotas_grupo = st.number_input(
        "Nº de cotas no grupo", min_value=2, value=int(d("num_cotas_grupo", 200)), step=10,
        help="Total de participantes (cotas) no grupo de consórcio — usado para estimar a chance de você ser sorteado a cada mês.",
    )
    cotas_sorteadas_por_mes = st.number_input("Cotas sorteadas por mês", min_value=1, value=1, step=1)

    st.markdown("---")


# ─────────────────────────────────────────────────────────────────────────────
# Cálculos
# ─────────────────────────────────────────────────────────────────────────────
consorcio = calcular_consorcio(
    valor_credito, prazo_meses, taxa_adm, fundo_reserva, seguro_perc,
    reajuste_anual=reajuste_anual, seguro_sobre_saldo=True,
)
financiamento = calcular_financiamento(valor_credito, taxa_financiamento, prazo_meses, consorcio.custo_total)
investimento = calcular_investimento(consorcio.parcelas, valor_credito, taxa_investimento, correcao_bem, prazo_meses)
lance = calcular_lance(consorcio.cronograma, perc_lance, mes_lance, prazo_meses, taxa_investimento, correcao_bem, tipo_lance=tipo_lance)
cet = calcular_cet(consorcio.parcelas, valor_credito, mes_contemplacao=mes_contemplacao_cet)
probabilidade = calcular_probabilidade_contemplacao(int(num_cotas_grupo), prazo_meses, int(cotas_sorteadas_por_mes))

meses_eixo = investimento.meses


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — exportação
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-title">Exportar</div>', unsafe_allow_html=True)

    nome_arquivo = cenario_sel
    for e in ["🎯", "🚗", "🚙", "🏍️", "🏠", "🏢", "🚚", " ", "/"]:
        nome_arquivo = nome_arquivo.replace(e, "_")
    nome_arquivo = nome_arquivo.strip("_")

    excel_buf = gerar_excel(
        cenario_sel=cenario_sel, valor_credito=valor_credito, prazo_meses=prazo_meses,
        taxa_adm=taxa_adm, fundo_reserva=fundo_reserva, seguro_perc=seguro_perc,
        reajuste_anual=reajuste_anual, perc_lance=perc_lance, mes_lance=mes_lance, tipo_lance=tipo_lance,
        taxa_financiamento=taxa_financiamento, taxa_investimento=taxa_investimento, correcao_bem=correcao_bem,
        consorcio=consorcio, financiamento=financiamento, investimento=investimento, lance=lance, cet=cet,
    )
    st.download_button(
        label="📥 Exportar para Excel", data=excel_buf,
        file_name=f"roi_consorcio_{nome_arquivo}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    pdf_buf = gerar_pdf_proposta(
        cenario_sel=cenario_sel, valor_credito=valor_credito, prazo_meses=prazo_meses,
        consorcio=consorcio, financiamento=financiamento, investimento=investimento, lance=lance, cet=cet,
    )
    st.download_button(
        label="📄 Exportar Proposta (PDF)", data=pdf_buf,
        file_name=f"proposta_consorcio_{nome_arquivo}.pdf",
        mime="application/pdf",
    )
    st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="header-tag">// Calculadora</div>', unsafe_allow_html=True)
st.title("Calculadora ROI de Consórcio")
if cenario_sel != "🎯 Personalizado":
    st.markdown(f'<span class="scenario-badge">{cenario_sel}</span>', unsafe_allow_html=True)
st.caption("Compare consórcio, financiamento, investir à vista, lance, CET e probabilidade de sorteio — em um só lugar.")
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

cet_label = fmt_pct_precisa(cet.cet_anual) if (cet.convergiu and cet.cet_anual is not None) else "N/D"

st.markdown(f"""
<div class="metrics-row">
  <div class="metric-card tall">
    <div class="metric-label">Parcela Consórcio (mês 1)</div>
    <div class="metric-value info">{fmt_brl(consorcio.parcela_inicial)}</div>
  </div>
  <div class="metric-card tall">
    <div class="metric-label">Custo Total Consórcio</div>
    <div class="metric-value warning">{fmt_brl(consorcio.custo_total)}</div>
  </div>
  <div class="metric-card tall">
    <div class="metric-label">CET Anualizado</div>
    <div class="{cor_card(cet.cet_anual if cet.cet_anual is not None else 0)}">{cet_label}</div>
  </div>
  <div class="metric-card tall">
    <div class="metric-label">Melhor Opção</div>
    <div class="metric-value wrap">{melhor_opcao}</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="disclaimer-box">
<p>⚠️ Ferramenta educacional. Taxas de administração, seguro, juros de financiamento, rendimento de investimento,
reajuste anual e correção do bem são estimativas informadas por você. Confira sempre as condições reais junto à
administradora de consórcio, ao banco e ao mercado antes de decidir. Esta calculadora não substitui uma simulação
oficial nem consultoria financeira.</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Layout comum dos gráficos Plotly
# ─────────────────────────────────────────────────────────────────────────────
def aplicar_layout(fig: go.Figure, y_titulo: str = "R$", y_prefixo: str = "R$ ") -> None:
    fig.update_layout(
        paper_bgcolor="#0a0a0f", plot_bgcolor="#0f0f1a",
        font=dict(family="Space Mono, monospace", color="#9ca3af", size=11),
        legend=dict(bgcolor="rgba(26,26,46,0.9)", bordercolor="#2d2d4e", borderwidth=1, font=dict(size=11)),
        xaxis=dict(title="Meses", gridcolor="#1e1e2e", zerolinecolor="#2d2d4e"),
        yaxis=dict(title=y_titulo, gridcolor="#1e1e2e", zerolinecolor="#2d2d4e", tickprefix=y_prefixo, tickformat=",.0f"),
        hovermode="x unified", margin=dict(l=10, r=10, t=20, b=10), height=380,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "💳 Financiamento", "📈 Investir à Vista", "🎯 Lance", "📊 CET",
    "🎲 Probabilidade", "📂 Comparar Administradoras", "🏠 Investir em Aluguel", "📖 Glossário",
])

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

    custo_acum_consorcio = []
    acumulado = 0.0
    for p in consorcio.parcelas:
        acumulado += p
        custo_acum_consorcio.append(acumulado)
    custo_acum_consorcio = [0.0] + custo_acum_consorcio

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=meses_eixo, y=custo_acum_consorcio,
                               name="Custo acumulado — Consórcio", line=dict(color="#4ade80", width=2.5)))
    fig1.add_trace(go.Scatter(x=meses_eixo, y=[financiamento.parcela * m for m in meses_eixo],
                               name="Custo acumulado — Financiamento", line=dict(color="#f87171", width=2.5, dash="dash")))
    aplicar_layout(fig1)
    st.plotly_chart(fig1, width='stretch')

    with st.expander("📋 Ver tabela mês a mês"):
        df1 = pd.DataFrame({
            "Mês": meses_eixo,
            "Custo Acumulado Consórcio": [f"R$ {v:,.2f}" for v in custo_acum_consorcio],
            "Custo Acumulado Financiamento": [f"R$ {financiamento.parcela*m:,.2f}" for m in meses_eixo],
            "Diferença": [f"R$ {(financiamento.parcela*m - c):,.2f}" for m, c in zip(meses_eixo, custo_acum_consorcio)],
        })
        st.dataframe(df1, width='stretch', hide_index=True)

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
      <div class="metric-card tall">
        <div class="metric-label">Bem Corrigido em {prazo_meses}m</div>
        <div class="metric-value warning">{fmt_brl(investimento.serie_bem_corrigido[-1])}</div>
      </div>
      <div class="metric-card tall">
        <div class="metric-label">Acumulado Investindo em {prazo_meses}m</div>
        <div class="metric-value info">{fmt_brl(investimento.serie_investido[-1])}</div>
      </div>
      <div class="metric-card tall">
        <div class="metric-label">Ganho Líquido Investindo</div>
        <div class="{cor_card(investimento.ganho_final)}">{fmt_brl(investimento.ganho_final)}</div>
      </div>
      <div class="metric-card tall">
        <div class="metric-label">Mês p/ Comprar à Vista</div>
        <div class="metric-value wrap">{fmt_meses(investimento.mes_cruzamento) if investimento.mes_cruzamento else "Fora do prazo"}</div>
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
    st.plotly_chart(fig2, width='stretch')

    with st.expander("📋 Ver tabela mês a mês"):
        df2 = pd.DataFrame({
            "Mês": meses_eixo,
            "Valor Investido Acumulado": [f"R$ {v:,.2f}" for v in investimento.serie_investido],
            "Valor do Bem Corrigido": [f"R$ {v:,.2f}" for v in investimento.serie_bem_corrigido],
            "Diferença": [f"R$ {(a-b):,.2f}" for a, b in zip(investimento.serie_investido, investimento.serie_bem_corrigido)],
        })
        st.dataframe(df2, width='stretch', hide_index=True)

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
    tipo_label = "Próprio (dinheiro extra)" if lance.tipo == "proprio" else "Embutido (parte do crédito)"
    st.markdown(f"""
    <div class="metrics-row">
      <div class="metric-card">
        <div class="metric-label">Tipo / Valor do Lance</div>
        <div class="metric-value warning">{fmt_brl(lance.valor_lance)}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Meses Antecipados</div>
        <div class="metric-value info">{lance.meses_antecipados}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Crédito Líquido Recebido</div>
        <div class="metric-value">{fmt_brl(lance.credito_liquido_recebido)}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Ganho Líquido do Lance</div>
        <div class="{cor_card(lance.ganho_liquido)}">{fmt_brl(lance.ganho_liquido)}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption(f"Tipo de lance selecionado: **{tipo_label}**")

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=meses_eixo, y=lance.serie_saldo_sem_lance, name="Saldo devedor — sem lance",
                               line=dict(color="#f87171", width=2.5, dash="dash")))
    fig3.add_trace(go.Scatter(x=meses_eixo, y=lance.serie_saldo_com_lance, name="Saldo devedor — com lance",
                               line=dict(color="#4ade80", width=2.5), fill="tozeroy", fillcolor="rgba(74,222,128,0.08)"))
    fig3.add_vline(x=mes_lance, line_dash="dot", line_color="#fb923c", line_width=1.5,
                    annotation_text=f"Lance: mês {mes_lance}",
                    annotation_font_color="#fb923c", annotation_position="top right")
    aplicar_layout(fig3)
    st.plotly_chart(fig3, width='stretch')

    with st.expander("📋 Ver tabela mês a mês"):
        df3 = pd.DataFrame({
            "Mês": meses_eixo,
            "Saldo Devedor sem Lance": [f"R$ {v:,.2f}" for v in lance.serie_saldo_sem_lance],
            "Saldo Devedor com Lance": [f"R$ {v:,.2f}" for v in lance.serie_saldo_com_lance],
        })
        st.dataframe(df3, width='stretch', hide_index=True)

    explicacao_tipo = (
        f"Como o lance é <strong>próprio</strong>, você desembolsa {fmt_brl(lance.valor_lance)} do próprio bolso — o crédito recebido continua integral, mas esse dinheiro deixa de render caso ficasse investido."
        if lance.tipo == "proprio" else
        f"Como o lance é <strong>embutido</strong>, {fmt_brl(lance.valor_lance)} saem do próprio crédito — você não desembolsa nada extra, mas recebe um crédito líquido de apenas {fmt_brl(lance.credito_liquido_recebido)}."
    )
    st.markdown(f"""
    <div class="summary-box">
    <p>
    Ofertando um lance no mês {mes_lance}, a contemplação sai do mês {prazo_meses}
    para o mês <strong>{lance.prazo_final_com_lance}</strong> — uma antecipação de <strong>{lance.meses_antecipados} meses</strong>.
    {explicacao_tipo}
    <br><br>
    Isso evita <strong>{fmt_brl(lance.beneficio_valorizacao_evitada)}</strong> em valorização do bem, contra um custo de oportunidade de
    <strong>{fmt_brl(lance.custo_oportunidade_lance)}</strong>. Ganho líquido estimado: <strong>{fmt_brl(lance.ganho_liquido)}</strong>
    {"— vale a pena antecipar." if lance.ganho_liquido >= 0 else "— nesse cenário, pode compensar mais não ofertar lance."}
    </p>
    </div>
    """, unsafe_allow_html=True)

# ── TAB 4: CET ────────────────────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-title">Custo Efetivo Total (CET)</div>', unsafe_allow_html=True)

    if cet.convergiu and cet.cet_mensal is not None and cet.cet_anual is not None:
        st.markdown(f"""
        <div class="metrics-row">
          <div class="metric-card">
            <div class="metric-label">CET Mensal</div>
            <div class="{cor_card(cet.cet_mensal)}">{fmt_pct_precisa(cet.cet_mensal)}</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">CET Anualizado</div>
            <div class="{cor_card(cet.cet_anual)}">{fmt_pct_precisa(cet.cet_anual)}</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Mês de Contemplação Assumido</div>
            <div class="metric-value">{cet.mes_contemplacao}</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Financiamento Equivalente</div>
            <div class="metric-value warning">{fmt_pct_precisa(((1+taxa_financiamento/100)**12-1)*100)}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        if cet.cet_anual >= 0:
            texto_cet = (
                f"Considerando contemplação no mês <strong>{cet.mes_contemplacao}</strong>, o consórcio tem um custo efetivo "
                f"equivalente a <strong>{fmt_pct_precisa(cet.cet_anual)} ao ano</strong> — "
                f"{'mais barato' if cet.cet_anual < ((1+taxa_financiamento/100)**12-1)*100 else 'mais caro'} "
                f"que o financiamento simulado ({fmt_pct_precisa(((1+taxa_financiamento/100)**12-1)*100)} a.a.)."
            )
        else:
            texto_cet = (
                f"Considerando contemplação apenas no mês <strong>{cet.mes_contemplacao}</strong>, o CET deu "
                f"<strong>negativo</strong> ({fmt_pct_precisa(cet.cet_anual)} a.a.) — isso acontece quando a contemplação "
                f"vem tarde: você já pagou quase tudo antes de receber o crédito, funcionando mais como uma poupança "
                f"com deságio do que como um financiamento antecipado."
            )
        st.markdown(f'<div class="summary-box"><p>{texto_cet}</p></div>', unsafe_allow_html=True)
    else:
        st.warning(
            f"⚠️ O CET não convergiu para o mês de contemplação escolhido (mês {mes_contemplacao_cet}). "
            "Isso é esperado matematicamente: o fluxo de caixa do consórcio tem um único aporte pontual "
            "(o crédito recebido) em vez de parcelas constantes como um empréstimo tradicional, então para "
            "meses de contemplação 'intermediários' pode não existir uma taxa real que zere o fluxo. "
            "Tente o cenário **Otimista (mês 1)** ou **Conservador (último mês)** na barra lateral."
        )

    st.markdown("""
    <div class="disclaimer-box">
    <p>📌 Metodologia: o CET é calculado como a Taxa Interna de Retorno (TIR) mensal do fluxo de caixa do
    participante — paga a parcela todo mês e recebe o crédito no mês de contemplação assumido — depois
    anualizada. "Otimista" (mês 1) é o cenário mais comparável a um financiamento tradicional (crédito recebido
    à vista). "Conservador" (último mês) mostra o pior caso, quando a contemplação só vem no fim do prazo.</p>
    </div>
    """, unsafe_allow_html=True)

# ── TAB 5: Probabilidade de sorteio ──────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-title">Probabilidade de Contemplação por Sorteio</div>', unsafe_allow_html=True)
    st.caption("Modelo simplificado: assume 1 sorteio por mês entre as cotas remanescentes, sem lances de terceiros nem saídas do grupo.")

    if probabilidade.meses:
        st.markdown(f"""
        <div class="metrics-row">
          <div class="metric-card">
            <div class="metric-label">Prob. no Mês 1</div>
            <div class="metric-value info">{fmt_pct_precisa(probabilidade.prob_mensal[0]*100)}</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Prob. Acumulada ao Fim</div>
            <div class="metric-value">{fmt_pct_precisa(probabilidade.prob_acumulada[-1]*100)}</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Mês p/ 50% de Chance</div>
            <div class="metric-value warning">{probabilidade.mes_50_perc if probabilidade.mes_50_perc else "Fora do prazo"}</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Mês p/ 90% de Chance</div>
            <div class="metric-value danger">{probabilidade.mes_90_perc if probabilidade.mes_90_perc else "Fora do prazo"}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        fig5 = go.Figure()
        fig5.add_trace(go.Scatter(x=probabilidade.meses, y=[p*100 for p in probabilidade.prob_acumulada],
                                   name="Probabilidade acumulada", line=dict(color="#4ade80", width=2.5),
                                   fill="tozeroy", fillcolor="rgba(74,222,128,0.08)"))
        aplicar_layout(fig5, y_titulo="Probabilidade (%)", y_prefixo="")
        fig5.update_yaxes(ticksuffix="%")
        st.plotly_chart(fig5, width='stretch')

        with st.expander("📋 Ver tabela mês a mês"):
            dfp = pd.DataFrame({
                "Mês": probabilidade.meses,
                "Probabilidade no Mês (%)": [f"{p*100:.3f}%" for p in probabilidade.prob_mensal],
                "Probabilidade Acumulada (%)": [f"{p*100:.2f}%" for p in probabilidade.prob_acumulada],
            })
            st.dataframe(dfp, width='stretch', hide_index=True)

        st.markdown(f"""
        <div class="summary-box">
        <p>
        Com <strong>{int(num_cotas_grupo)} cotas</strong> no grupo e {int(cotas_sorteadas_por_mes)} sorteio(s) por mês,
        um participante tem <strong>{fmt_pct_precisa(probabilidade.prob_acumulada[-1]*100)}</strong> de chance acumulada
        de ser contemplado por sorteio (sem lance) ao longo dos {prazo_meses} meses do grupo.
        {"Metade dos participantes tende a ser contemplada até o mês <strong>"+str(probabilidade.mes_50_perc)+"</strong>." if probabilidade.mes_50_perc else "Neste cenário, menos de 50% dos participantes seriam contemplados só por sorteio dentro do prazo — lances tendem a ser necessários."}
        </p>
        </div>
        """, unsafe_allow_html=True)

# ── TAB 6: Comparador de administradoras via CSV ─────────────────────────────
with tab6:
    st.markdown('<div class="section-title">Comparar Administradoras via CSV</div>', unsafe_allow_html=True)
    st.caption("Envie um CSV com propostas de diferentes administradoras para rankear por CET (menor custo primeiro).")

    csv_exemplo = gerar_csv_exemplo()
    st.download_button(
        "📥 Baixar modelo de CSV de exemplo", data=csv_exemplo,
        file_name="modelo_administradoras.csv", mime="text/csv",
    )

    cenario_cet_comparador = st.radio(
        "Cenário de contemplação para o CET do comparador",
        options=["otimista", "conservador"],
        format_func=lambda x: "🟢 Otimista (mês 1)" if x == "otimista" else "🔴 Conservador (último mês)",
        horizontal=True,
    )

    arquivo_csv = st.file_uploader("Envie o CSV de propostas", type=["csv"])
    if arquivo_csv is not None:
        try:
            resultados = comparar_administradoras(arquivo_csv.getvalue(), mes_contemplacao_cet=cenario_cet_comparador)
            df_comp = pd.DataFrame([{
                "Administradora": r.administradora,
                "Crédito": fmt_brl(r.valor_credito) if not r.erro else "-",
                "Prazo (meses)": r.prazo_meses if not r.erro else "-",
                "Parcela Média": fmt_brl(r.parcela_media) if not r.erro else "-",
                "Custo Total": fmt_brl(r.custo_total) if not r.erro else "-",
                "CET Anual": fmt_pct_precisa(r.cet_anual) if r.cet_anual is not None else "N/D",
                "Erro": r.erro or "",
            } for r in resultados])
            st.dataframe(df_comp, width='stretch', hide_index=True)

            validos = [r for r in resultados if r.cet_anual is not None]
            if validos:
                melhor = validos[0]
                st.success(f"🏆 Melhor CET: **{melhor.administradora}** com {fmt_pct_precisa(melhor.cet_anual)} ao ano.")
        except ComparadorCSVError as e:
            st.error(f"❌ Erro no CSV enviado: {e}")
        except Exception as e:  # noqa: BLE001 — feedback amigável para qualquer erro de parsing
            st.error(f"❌ Não foi possível processar o CSV: {e}")

# ── TAB 7: Investir em Aluguel (consórcio imobiliário como investimento) ─────
with tab7:
    st.markdown('<div class="section-title">Consórcio Imobiliário como Investimento</div>', unsafe_allow_html=True)
    st.caption(
        "Caso de uso diferente do resto da calculadora: em vez de usar o bem, você usa o consórcio para "
        "comprar um imóvel e colocá-lo para alugar, projetando o retorno em um horizonte de longo prazo."
    )

    with st.expander("⚙️ Parâmetros do Investimento", expanded=True):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Consórcio**")
            inv_valor_credito = st.number_input("Valor do crédito (R$)", min_value=10000.0, value=500000.0, step=10000.0, key="inv_valor_credito")
            inv_prazo_meses = st.slider("Prazo do grupo (meses)", 60, 240, value=200, key="inv_prazo_meses")
            inv_taxa_adm = st.number_input("Taxa de administração total (%)", min_value=0.0, value=18.0, step=0.5, key="inv_taxa_adm")
            inv_fundo_reserva = st.number_input("Fundo de reserva (%)", min_value=0.0, value=2.0, step=0.5, key="inv_fundo_reserva")
            inv_seguro_perc = st.number_input("Seguro mensal (% do saldo devedor)", min_value=0.0, value=0.0, step=0.01, format="%.3f", key="inv_seguro_perc")
            inv_reajuste_anual = st.number_input("Reajuste anual do consórcio — INCC/IPCA (%)", min_value=0.0, value=0.0, step=0.5, key="inv_reajuste_anual")

            st.markdown("**Contemplação e Lance**")
            inv_mes_contemplacao = st.slider("Mês da contemplação (via lance)", 1, inv_prazo_meses, value=min(24, inv_prazo_meses), key="inv_mes_contemplacao")
            inv_perc_lance = st.number_input("Lance ofertado (% do crédito)", min_value=0.0, max_value=100.0, value=30.0, step=1.0, key="inv_perc_lance")
            inv_tipo_lance = st.radio(
                "Tipo de lance", options=["proprio", "embutido"],
                format_func=lambda x: "💰 Próprio (dinheiro extra)" if x == "proprio" else "📉 Embutido (parte do crédito)",
                index=1, horizontal=True, key="inv_tipo_lance",
            )

        with col_b:
            st.markdown("**Aquisição e Manutenção**")
            inv_itbi_perc = st.number_input("ITBI + escritura (% do valor do bem)", min_value=0.0, value=4.0, step=0.5, key="inv_itbi_perc")
            inv_manutencao = st.number_input("Manutenção/condomínio mensal (R$)", min_value=0.0, value=400.0, step=50.0, key="inv_manutencao")

            st.markdown("**Locação**")
            inv_yield_aluguel = st.number_input("Yield de aluguel (% do valor do imóvel/mês)", min_value=0.0, value=0.45, step=0.05, key="inv_yield_aluguel")
            inv_reajuste_aluguel = st.number_input("Reajuste do aluguel — IPCA (% a.a.)", min_value=0.0, value=4.5, step=0.5, key="inv_reajuste_aluguel")

            st.markdown("**Valorização e Horizonte**")
            inv_valorizacao_anual = st.number_input("Valorização imobiliária (% a.a.)", min_value=0.0, value=5.0, step=0.5, key="inv_valorizacao_anual")
            inv_horizonte_anos = st.slider("Horizonte total da simulação (anos)", 10, 40, value=20, key="inv_horizonte_anos")

    inv_consorcio = calcular_consorcio(
        inv_valor_credito, inv_prazo_meses, inv_taxa_adm, inv_fundo_reserva, inv_seguro_perc,
        reajuste_anual=inv_reajuste_anual, seguro_sobre_saldo=True,
    )
    inv = calcular_investimento_imovel(
        valor_credito=inv_valor_credito,
        cronograma_consorcio=inv_consorcio.cronograma,
        prazo_meses=inv_prazo_meses,
        mes_contemplacao=inv_mes_contemplacao,
        perc_lance=inv_perc_lance,
        tipo_lance=inv_tipo_lance,
        itbi_escritura_perc=inv_itbi_perc,
        manutencao_mensal=inv_manutencao,
        yield_aluguel_mensal=inv_yield_aluguel,
        reajuste_aluguel_anual=inv_reajuste_aluguel,
        valorizacao_imobiliaria_anual=inv_valorizacao_anual,
        horizonte_anos=inv_horizonte_anos,
    )

    st.markdown(f'<div class="section-title">Fluxo de Caixa Detalhado ({inv_horizonte_anos} Anos)</div>', unsafe_allow_html=True)
    st.markdown(
        f"O fluxo de caixa projeta mês a mês os desembolsos e recebimentos ao longo de todo o período do "
        f"consórcio e além, até completar {inv_horizonte_anos} anos de operação."
    )

    fase1_parcela_mes = inv_consorcio.cronograma[0].parcela if inv_consorcio.cronograma else 0.0
    tipo_lance_label = "próprio (dinheiro extra)" if inv_tipo_lance == "proprio" else "embutido (parte do crédito)"

    st.markdown(f"""
    <div class="summary-box">
    <p><strong>Fase 1 — Pré-Contemplação (meses {inv.fase1.mes_inicio} a {inv.fase1.mes_fim})</strong><br>
    Desembolso mensal: {fmt_brl(fase1_parcela_mes)} (parcela do consórcio)<br>
    Total desembolsado: {fmt_brl(inv.fase1.desembolso_total)}<br>
    Lance ofertado no mês {inv.mes_contemplacao}: {fmt_brl(inv.valor_lance)} ({tipo_lance_label})<br>
    Recebimento: nenhum (ainda não há imóvel)</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    aluguel_inicial_fase2 = inv_valor_credito * (inv_yield_aluguel / 100)
    parcela_fase2_mes = inv_consorcio.cronograma[inv.mes_contemplacao].parcela if inv.mes_contemplacao < len(inv_consorcio.cronograma) else 0.0
    meses_fase2 = max(inv.fase2.mes_fim - inv.fase2.mes_inicio + 1, 0)
    st.markdown(f"""
    <div class="summary-box">
    <p><strong>Fase 2 — Locação + Parcelas (meses {inv.fase2.mes_inicio} a {inv.fase2.mes_fim})</strong><br>
    Desembolso mensal inicial: {fmt_brl(parcela_fase2_mes)} (parcela) + {fmt_brl(inv_manutencao)} (manutenção/condomínio)<br>
    Recebimento mensal inicial (aluguel): {fmt_brl(aluguel_inicial_fase2)} (crescente com reajuste anual)<br>
    Aluguel acumulado ({meses_fase2} meses): {fmt_brl(inv.fase2.recebimento_total)}<br>
    Desembolso total da fase 2: {fmt_brl(inv.fase2.desembolso_total)}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    meses_fase3 = max(inv.fase3.mes_fim - inv.fase3.mes_inicio + 1, 0)
    aluguel_final = inv.serie_aluguel[-1] if inv.serie_aluguel else 0.0
    st.markdown(f"""
    <div class="summary-box">
    <p><strong>Fase 3 — Renda Líquida (meses {inv.fase3.mes_inicio} a {inv.fase3.mes_fim})</strong><br>
    Parcela do consórcio: R$ 0 (quitado)<br>
    Aluguel mensal ao final do horizonte (reajustado): {fmt_brl(aluguel_final)}<br>
    Renda líquida ({meses_fase3} meses): {fmt_brl(inv.fase3.recebimento_total)}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    fig_inv = go.Figure()
    fig_inv.add_trace(go.Scatter(
        x=inv.serie_meses, y=inv.serie_patrimonio_acumulado, name="Fluxo de caixa acumulado",
        line=dict(color="#4ade80", width=2.5), fill="tozeroy", fillcolor="rgba(74,222,128,0.08)",
    ))
    fig_inv.add_vline(x=inv.mes_contemplacao, line_dash="dot", line_color="#fb923c", line_width=1.5,
                       annotation_text="Contemplação", annotation_font_color="#fb923c", annotation_position="top left")
    fig_inv.add_vline(x=inv_prazo_meses, line_dash="dot", line_color="#60a5fa", line_width=1.5,
                       annotation_text="Consórcio quitado", annotation_font_color="#60a5fa", annotation_position="top left")
    aplicar_layout(fig_inv)
    st.plotly_chart(fig_inv, width='stretch')

    with st.expander("📋 Ver tabela mês a mês"):
        df_inv = pd.DataFrame({
            "Mês": inv.serie_meses,
            "Fluxo Líquido do Mês": [f"R$ {v:,.2f}" for v in inv.serie_fluxo_liquido],
            "Aluguel Recebido": [f"R$ {v:,.2f}" for v in inv.serie_aluguel],
            "Fluxo Acumulado": [f"R$ {v:,.2f}" for v in inv.serie_patrimonio_acumulado],
        })
        st.dataframe(df_inv, width='stretch', hide_index=True)

    st.markdown(f'<div class="section-title">Resumo Financeiro em {inv_horizonte_anos} Anos</div>', unsafe_allow_html=True)
    tir_label = fmt_pct_precisa(inv.tir_anual_pct) if (inv.tir_convergiu and inv.tir_anual_pct is not None) else "N/D"
    st.markdown(f"""
    <div class="metrics-row">
      <div class="metric-card">
        <div class="metric-label">Total Desembolsado</div>
        <div class="metric-value warning">{fmt_brl(inv.total_desembolsado)}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Aluguéis Recebidos</div>
        <div class="metric-value info">{fmt_brl(inv.alugueis_recebidos)}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Valor do Imóvel Final</div>
        <div class="metric-value">{fmt_brl(inv.valor_imovel_final)}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Patrimônio Total Gerado</div>
        <div class="{cor_card(inv.patrimonio_total)}">{fmt_brl(inv.patrimonio_total)}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="metrics-row">
      <div class="metric-card">
        <div class="metric-label">ROI Total ({inv_horizonte_anos} anos)</div>
        <div class="{cor_card(inv.roi_total_pct)}">{fmt_pct(inv.roi_total_pct)}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">ROI Anualizado</div>
        <div class="{cor_card(inv.roi_anualizado_pct)}">{fmt_pct_precisa(inv.roi_anualizado_pct)}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">TIR Anualizada</div>
        <div class="metric-value">{tir_label}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Mês da Contemplação</div>
        <div class="metric-value">{inv.mes_contemplacao}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if not inv.tir_convergiu:
        st.warning(
            "⚠️ A TIR não convergiu para este cenário — propriedade matemática do fluxo de caixa "
            "(múltiplas trocas de sinal), não um erro. O ROI total e o ROI anualizado acima continuam válidos."
        )

    st.markdown("""
    <div class="disclaimer-box">
    <p>📌 Esta aba modela um caso de uso diferente do restante da calculadora: comprar um imóvel via
    consórcio para <strong>alugar</strong> (gerar renda), não para uso próprio. A metodologia — 3 fases,
    yield de aluguel sobre o valor do crédito, reajuste anual do aluguel pelo IPCA, valorização imobiliária
    separada do reajuste do saldo devedor — é inspirada em simulações de mercado, mas os números são
    projeções sensíveis às premissas que você ajustar acima. Valores brutos: não considera Imposto de Renda
    sobre aluguel nem ganho de capital na venda. Ferramenta educacional — não substitui consultoria
    financeira ou imobiliária.</p>
    </div>
    """, unsafe_allow_html=True)

# ── TAB 8: Glossário ──────────────────────────────────────────────────────────
with tab8:
    st.markdown('<div class="section-title">Glossário do Consórcio</div>', unsafe_allow_html=True)
    for item in GLOSSARIO:
        with st.expander(f"📖 {item['termo']}"):
            st.write(item["definicao"])

st.markdown("<br>", unsafe_allow_html=True)
st.caption("Calculadora educacional de ROI de Consórcio.")
