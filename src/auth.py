"""
Tela de acesso — gate por senha única.

A senha esperada vem de `st.secrets["app_password"]` (arquivo local
`.streamlit/secrets.toml`, não versionado, ou "Secrets" do Streamlit
Community Cloud em produção).
"""

import hmac

import streamlit as st

CHAVE_SECRETA = "app_password"
CHAVE_SESSAO = "autenticado"


def senha_valida(candidata: str, esperada: str) -> bool:
    """Compara senhas em tempo constante; nunca valida contra senha vazia."""
    if not esperada:
        return False
    return hmac.compare_digest(candidata, esperada)


def exigir_login() -> None:
    """Bloqueia o restante da página até a senha correta ser informada."""
    if st.session_state.get(CHAVE_SESSAO):
        return

    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        st.markdown(
            """
            <div class="login-card">
                <div class="login-icon">🏦</div>
                <div class="login-title">ROI de Consórcio</div>
                <div class="login-subtitle">Acesso restrito — digite a senha para continuar</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("form_login"):
            senha = st.text_input(
                "Senha", type="password", label_visibility="collapsed",
                placeholder="Digite a senha de acesso",
            )
            enviado = st.form_submit_button("Entrar", use_container_width=True)

        if enviado:
            esperada = str(st.secrets.get(CHAVE_SECRETA, ""))
            if senha_valida(senha, esperada):
                st.session_state[CHAVE_SESSAO] = True
                st.rerun()
            elif not esperada:
                st.error(
                    "Senha de acesso não configurada. Defina `app_password` em "
                    "`.streamlit/secrets.toml` (local) ou em Settings → Secrets (Streamlit Cloud)."
                )
            else:
                st.error("Senha incorreta.")

    st.stop()
