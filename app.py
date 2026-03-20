'''import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from utils.helpers import PHOTO_PATH, PROF_NAME
from database import init_db, validate_session, load_students
from ui_helpers import init_session, inject_global_css, show_sidebar, js_save_session
from guards.auth_helper import get_auth

st.set_page_config(
    page_title="Tati's Voice English Class",
    page_icon=str(Path(PHOTO_PATH)) if Path(PHOTO_PATH).exists() else "🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    '<link rel="stylesheet" '
    'href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">',
    unsafe_allow_html=True,
)
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover, maximum-scale=1.0, user-scalable=no">
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

if not st.session_state.get("_db_initialized"):
    init_db()
    st.session_state["_db_initialized"] = True
init_session()
inject_global_css()

auth = get_auth()


def main():

    # ── Já logado nesta sessão ────────────────────────────────────────────────
    if st.session_state.logged_in:
        _render_page()
        return

    # ── Aguarda CookieController carregar (precisa de 1 rerun) ────────────────
    if not st.session_state.get("_cookie_checked"):
        st.session_state["_cookie_checked"] = True
        # Mostra tela preta enquanto verifica — sem flash de login
        st.markdown(
            "<div style='position:fixed;inset:0;background:#060a10;z-index:9999;'></div>",
            unsafe_allow_html=True,
        )
        st.rerun()
        return

    # ── Tenta cookie ──────────────────────────────────────────────────────────
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
                st.session_state.page              = "dashboard" if user_data["role"] in ("professor", "programador", "professora", "Professora", "Tatiana", "Tati") else "voice"
                st.session_state.conv_id           = None
                st.session_state["_session_token"] = token
                st.rerun()
                return
        auth.clear()

    # ── Fallback query param ──────────────────────────────────────────────────
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
                st.session_state.page              = "dashboard" if user_data["role"] in ("professor", "programador", "professora", "Professora", "Tatiana", "Tati") else "voice"
                st.session_state.conv_id           = None
                st.session_state["_session_token"] = _s
                auth.save(_s)
                st.rerun()
                return
        st.query_params.pop("s", None)

    # ── Mostra login ──────────────────────────────────────────────────────────
    from tati_views.login import show_login
    show_login(auth)


def _render_page():
    token = st.session_state.get("_session_token", "")
    if token and not st.session_state.get("_session_saved"):
        js_save_session(token)
        st.session_state["_session_saved"] = True

    show_sidebar()

    page = st.session_state.page
    role = st.session_state.user.get("role", "")

    if page == "voice":
        from tati_views.voice import show_voice
        show_voice()
    elif page == "settings":
        from tati_views.settings import show_settings
        show_settings()
    elif page == "history":
        from tati_views.history import show_history
        show_history()
    elif page == "dashboard" and role in ("professor", "programador", "professora", "Professora", "Tatiana", "Tati"):
        from tati_views.dashboard import show_dashboard
        show_dashboard()
    else:
        st.session_state.page = "voice"
        st.rerun()


main()'''

import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from utils.helpers import PHOTO_PATH, PROF_NAME
from database import init_db, validate_session, load_students
from ui_helpers import init_session, inject_global_css, show_sidebar, js_save_session
from guards.auth_helper import get_auth

st.set_page_config(
    page_title="Tati's Voice English Class",
    page_icon=str(Path(PHOTO_PATH)) if Path(PHOTO_PATH).exists() else "🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    '<link rel="stylesheet" '
    'href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">',
    unsafe_allow_html=True,
)
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover, maximum-scale=1.0, user-scalable=no">
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

if not st.session_state.get("_db_initialized"):
    init_db()
    st.session_state["_db_initialized"] = True
init_session()
inject_global_css()

auth = get_auth()

# Roles com acesso ao dashboard — inclui todas as variações do nome da professora
_PROF_ROLES  = ("professor", "programador", "professora", "Professora", "Tatiana", "Tati")
_VALID_PAGES = {"voice", "history", "settings", "dashboard"}


def _sync_page_from_url() -> None:
    """
    Lê ?page= da URL e sincroniza com st.session_state.page.
    Garante que dashboard só é acessível para roles autorizados.
    Se ?page= não estiver na URL, mantém o estado atual sem alterar.
    """
    qp = st.query_params.get("page", "")
    if qp in _VALID_PAGES:
        if qp == "dashboard":
            role = st.session_state.user.get("role", "") if st.session_state.get("user") else ""
            if role not in _PROF_ROLES:
                qp = "voice"
        st.session_state.page = qp


def _inject_page_data_attr() -> None:
    """
    Injeta data-page="<nome>" no <body> via JS.
    Permite controle de CSS por página sem tocar no Python:
        body[data-page="history"]  { ... }
        body[data-page="settings"] { ... }
        body[data-page="voice"]    section[data-testid="stMain"] { overflow: hidden }
    """
    page = st.session_state.get("page", "voice")
    st.markdown(f"""
<script>
(function(){{
    var doc = window.parent ? window.parent.document : document;
    doc.body.setAttribute('data-page', '{page}');
}})();
</script>""", unsafe_allow_html=True)


def main():

    # ── Já logado nesta sessão ────────────────────────────────────────────────
    if st.session_state.logged_in:
        _sync_page_from_url()
        _render_page()
        return

    # ── Aguarda CookieController carregar (precisa de 1 rerun) ────────────────
    if not st.session_state.get("_cookie_checked"):
        st.session_state["_cookie_checked"] = True
        # Mostra tela preta enquanto verifica — sem flash de login
        st.markdown(
            "<div style='position:fixed;inset:0;background:#060a10;z-index:9999;'></div>",
            unsafe_allow_html=True,
        )
        st.rerun()
        return

    # ── Tenta cookie ──────────────────────────────────────────────────────────
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
                st.session_state.page              = "dashboard" if user_data["role"] in _PROF_ROLES else "voice"
                st.session_state.conv_id           = None
                st.session_state["_session_token"] = token
                st.rerun()
                return
        auth.clear()

    # ── Fallback query param ?s= (auto-login via localStorage) ───────────────
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
                st.session_state.page              = "dashboard" if user_data["role"] in _PROF_ROLES else "voice"
                st.session_state.conv_id           = None
                st.session_state["_session_token"] = _s
                auth.save(_s)
                st.rerun()
                return
        st.query_params.pop("s", None)

    # ── Mostra login ──────────────────────────────────────────────────────────
    from tati_views.login import show_login
    show_login(auth)


def _render_page():
    token = st.session_state.get("_session_token", "")
    if token and not st.session_state.get("_session_saved"):
        js_save_session(token)
        st.session_state["_session_saved"] = True

    # Injeta data-page no body para controle CSS por página
    _inject_page_data_attr()

    show_sidebar()

    page = st.session_state.page
    role = st.session_state.user.get("role", "")

    if page == "voice":
        from tati_views.voice import show_voice
        show_voice()
    elif page == "settings":
        from tati_views.settings import show_settings
        show_settings()
    elif page == "history":
        from tati_views.history import show_history
        show_history()
    elif page == "dashboard" and role in _PROF_ROLES:
        from tati_views.dashboard import show_dashboard
        show_dashboard()
    else:
        st.session_state.page = "voice"
        st.query_params["page"] = "voice"
        st.rerun()


main()