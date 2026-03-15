"""
PATCH para ui_helpers.py — função _logout() integrada com AuthHelper.
Substitua a função _logout() existente por esta versão.
"""

from guards.auth_helper import AuthHelper
_auth = AuthHelper()


def _logout():
    """Limpa sessão, cookie HMAC e localStorage."""
    from database import delete_session
    import streamlit.components.v1 as components

    token = st.session_state.get("_session_token", "")
    if token:
        delete_session(token)

    # Apaga o cookie HMAC
    _auth.clear()

    # Apaga o localStorage legado
    components.html("""<!DOCTYPE html><html><head>
<style>html,body{margin:0;padding:0;overflow:hidden;}</style>
</head><body><script>
(function(){
    try{window.parent.localStorage.removeItem('pav_session');}catch(e){}
    try{localStorage.removeItem('pav_session');}catch(e){}
})();
</script></body></html>""", height=1)

    # Limpa session_state
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    for k, v in SESSION_DEFAULTS.items():
        st.session_state[k] = v
    st.session_state.pop("_session_saved", None)


# ─────────────────────────────────────────────────────────────────────────────
# PATCH para app.py — bloco de auto-login no router main()
# Substitua o bloco "Tenta auto-login via query param" por este:
# ─────────────────────────────────────────────────────────────────────────────

"""
def main():
    # ── Auto-login: cookie HMAC (prioridade) ou query param ──────────────────
    if not st.session_state.logged_in:

        # 1. Tenta pelo cookie HMAC — mais seguro e não expõe token na URL
        from tati_views.login import try_cookie_login
        if try_cookie_login():
            st.rerun()
            return

        # 2. Fallback: query param ?s=token (compatibilidade)
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

    # ... resto do main() igual
"""
