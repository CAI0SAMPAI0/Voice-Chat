"""
app.py — Teacher Tati · Entry point
Responsabilidade única: inicializar, autenticar sessão e rotear para a página certa.
Toda lógica de UI está em pages/ e ui_helpers.py.
"""

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
from views.login     import show_login
from views.voice     import show_voice
from views.settings  import show_settings
from views.history   import show_history
from views.dashboard import show_dashboard

# ── Page config — deve ser a primeira chamada Streamlit ──────────────────────
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
    # ── Tenta auto-login via query param ?s=token ────────────────────────────
    if not st.session_state.logged_in:
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
                    st.rerun()
            else:
                st.query_params.pop("s", None)

        show_login()
        return

    # ── Persiste token na URL / localStorage ─────────────────────────────────
    token = st.session_state.get("_session_token", "")
    if token and st.query_params.get("s") != token:
        st.query_params["s"] = token
    if token and not st.session_state.get("_session_saved"):
        js_save_session(token)
        st.session_state["_session_saved"] = True

    # ── Sidebar ───────────────────────────────────────────────────────────────
    show_sidebar()

    # ── Roteamento ────────────────────────────────────────────────────────────
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