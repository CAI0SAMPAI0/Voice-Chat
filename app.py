"""
app.py — Teacher Tati · Entry point
"""

import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st

from database import init_db, validate_session, load_students
from ui_helpers import init_session, inject_global_css, show_sidebar, js_save_session
from guards.auth_helper import get_auth

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
<meta name="viewport" content="width=device-width,initial-scale=1.0,viewport-fit=cover,maximum-scale=1.0">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
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

# ── Instância única do AuthHelper (CookieController) ─────────────────────────
auth = get_auth()


# =============================================================================
# ROUTER
# =============================================================================
def main():

    # ── Já logado nesta sessão — vai direto ───────────────────────────────────
    if st.session_state.logged_in:
        _render_page()
        return

    # ── Tenta auto-login via cookie ───────────────────────────────────────────
    # O CookieController precisa de um ciclo de renderização para carregar.
    # Usamos uma flag para saber se já esperamos esse ciclo.
    if not st.session_state.get("_cookie_checked"):
        # Primeiro rerun: marca que já vamos checar, espera o componente carregar
        st.session_state["_cookie_checked"] = True
        st.rerun()
        return

    # Segundo rerun: agora o CookieController já carregou, podemos ler
    token = auth.get_token()
    if token:
        user_data = validate_session(token)
        if user_data:
            username = user_data.get("_resolved_username") or next(
                (k for k, v in load_students().items()
                 if v["password"] == user_data["password"]),
                None,
            )
            if username:
                st.session_state.logged_in         = True
                st.session_state.user              = {"username": username, **user_data}
                st.session_state.page              = "dashboard" if user_data["role"] == "professor" else "voice"
                st.session_state.conv_id           = None
                st.session_state["_session_token"] = token
                st.rerun()
                return
        # Token inválido — limpa e mostra login
        auth.clear()

    # ── Fallback: query param ?s=token ────────────────────────────────────────
    _s = st.query_params.get("s", "")
    if _s and len(_s) > 10:
        user_data = validate_session(_s)
        if user_data:
            username = user_data.get("_resolved_username") or next(
                (k for k, v in load_students().items()
                 if v["password"] == user_data["password"]),
                None,
            )
            if username:
                st.session_state.logged_in         = True
                st.session_state.user              = {"username": username, **user_data}
                st.session_state.page              = "dashboard" if user_data["role"] == "professor" else "voice"
                st.session_state.conv_id           = None
                st.session_state["_session_token"] = _s
                auth.save(_s)
                st.rerun()
                return
        st.query_params.pop("s", None)

    # ── Nenhum auto-login — mostra tela de login ──────────────────────────────
    from tati_views.login import show_login
    show_login(auth)


def _render_page():
    token = st.session_state.get("_session_token", "")
    if token and not st.session_state.get("_session_saved"):
        js_save_session(token)
        st.session_state["_session_saved"] = True

    show_sidebar()

    page = st.session_state.page
    if page == "voice":
        from tati_views.voice import show_voice
        show_voice()
    elif page == "settings":
        from tati_views.settings import show_settings
        show_settings()
    elif page == "history":
        from tati_views.history import show_history
        show_history()
    elif page == "dashboard" and st.session_state.user.get("role") == "professor":
        from tati_views.dashboard import show_dashboard
        show_dashboard()
    else:
        st.session_state.page = "voice"
        st.rerun()


main()