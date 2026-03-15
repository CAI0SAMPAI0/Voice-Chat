"""
app.py — Teacher Tati · Entry point
Responsabilidade única: inicializar, autenticar sessão e rotear para a página certa.
"""
from guards.auth_helper import AuthHelper
auth = AuthHelper()   # ← UMA instância global

# passa para as funções que precisam
from tati_views.login import show_login
show_login(auth)      # ← recebe auth como parâmetro
import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import streamlit.components.v1 as components

from database import init_db, validate_session, load_students
from ui_helpers import (
    init_session,
    inject_global_css,
    show_sidebar,
    js_save_session,
    SESSION_DEFAULTS,
)
from tati_views.login     import show_login, try_cookie_login
from tati_views.voice     import show_voice
from tati_views.settings  import show_settings
from tati_views.history   import show_history
from tati_views.dashboard import show_dashboard

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Tati's Voice English Class",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Assets globais ────────────────────────────────────────────────────────────
st.markdown(
    '<link rel="stylesheet" '
    'href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">',
    unsafe_allow_html=True,
)
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover, maximum-scale=1.0">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<style>
html { height: 100dvh; }
body { min-height: 100dvh; background: #060a10 !important; }
.stApp { min-height: 100dvh !important; }
@supports(padding: max(0px)) {
    .mic-footer { padding-bottom: max(20px, env(safe-area-inset-bottom)) !important; }
}
</style>
""", unsafe_allow_html=True)

# ── Init ──────────────────────────────────────────────────────────────────────
init_db()
init_session()
inject_global_css()


# =============================================================================
# ROUTER
# =============================================================================
def main():

    # ── Placeholder vazio — bloqueia renderização prematura ──────────────────
    # Enquanto verificamos o estado de autenticação, não renderizamos nada.
    # Isso evita o "flash" de tela errada que você viu na imagem.
    placeholder = st.empty()

    # ── 1. Já logado nesta sessão — vai direto para a página ─────────────────
    if st.session_state.logged_in:
        placeholder.empty()   # limpa o placeholder antes de renderizar
        _render_page()
        return

    # ── 2. Tenta auto-login via cookie HMAC ───────────────────────────────────
    with placeholder.container():
        # Mostra tela preta enquanto verifica — sem flash de login
        st.markdown(
            "<div style='height:100vh;background:#060a10;'></div>",
            unsafe_allow_html=True,
        )

    if try_cookie_login():
        placeholder.empty()
        st.rerun()
        return

    # ── 3. Tenta auto-login via query param ?s=token (fallback legado) ────────
    _s = st.query_params.get("s", "")
    if _s and len(_s) > 10:
        _ud = validate_session(_s)
        if _ud:
            _un = _ud.get("_resolved_username") or next(
                (k for k, v in load_students().items() if v["password"] == _ud["password"]),
                None,
            )
            if _un:
                st.session_state.logged_in         = True
                st.session_state.user              = {"username": _un, **_ud}
                st.session_state.page              = "dashboard" if _ud["role"] == "professor" else "voice"
                st.session_state.conv_id           = None
                st.session_state["_session_token"] = _s
                placeholder.empty()
                st.rerun()
                return
        else:
            st.query_params.pop("s", None)

    # ── 4. Nenhum auto-login funcionou — mostra tela de login ─────────────────
    placeholder.empty()
    show_login()


def _render_page():
    """Renderiza a página correta após autenticação confirmada."""

    # Persiste token na URL / localStorage
    token = st.session_state.get("_session_token", "")
    if token and st.query_params.get("s") != token:
        st.query_params["s"] = token
    if token and not st.session_state.get("_session_saved"):
        js_save_session(token)
        st.session_state["_session_saved"] = True

    # Sidebar
    show_sidebar()

    # Roteamento
    page = st.session_state.page

    if page == "voice":
        show_voice()
    elif page == "settings":
        show_settings()
    elif page == "history":
        show_history()
    elif page == "dashboard" and st.session_state.user.get("role") == "professor":
        show_dashboard()
    else:
        st.session_state.page = "voice"
        st.rerun()


main()