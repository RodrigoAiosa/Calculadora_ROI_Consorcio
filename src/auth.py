"""
Tela de acesso — login com nome + senha única.

A senha esperada vem de `st.secrets["app_password"]` (arquivo local
`.streamlit/secrets.toml`, não versionado, ou "Secrets" do Streamlit
Community Cloud em produção). O nome é só para identificar/saudar quem
entrou — não há contas individuais.
"""

import html
import hmac

import streamlit as st

CHAVE_SECRETA = "app_password"
CHAVE_SESSAO = "autenticado"
CHAVE_NOME = "usuario_nome"


def senha_valida(candidata: str, esperada: str) -> bool:
    """Compara senhas em tempo constante; nunca valida contra senha vazia."""
    if not esperada:
        return False
    return hmac.compare_digest(candidata, esperada)


def exigir_login() -> None:
    """Bloqueia o restante da página até nome + senha corretos serem informados."""
    if st.session_state.get(CHAVE_SESSAO):
        return

    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        st.markdown(
            """
            <div class="login-header">
                <div class="login-icon">🏦</div>
                <div class="login-title">ROI de Consórcio</div>
                <div class="login-subtitle">Acesso restrito · entre com seu nome e senha</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("form_login"):
            nome = st.text_input("Nome", placeholder="Seu nome")
            senha = st.text_input("Senha", type="password", placeholder="••••••••")
            enviado = st.form_submit_button("Entrar", use_container_width=True)

        if enviado:
            nome_limpo = nome.strip()
            esperada = str(st.secrets.get(CHAVE_SECRETA, ""))
            if not nome_limpo:
                st.error("Informe seu nome.")
            elif not esperada:
                st.error(
                    "Senha de acesso não configurada. Defina `app_password` em "
                    "`.streamlit/secrets.toml` (local) ou em Settings → Secrets (Streamlit Cloud)."
                )
            elif senha_valida(senha, esperada):
                st.session_state[CHAVE_SESSAO] = True
                st.session_state[CHAVE_NOME] = html.escape(nome_limpo)
                st.rerun()
            else:
                st.error("Senha incorreta.")

    st.stop()
