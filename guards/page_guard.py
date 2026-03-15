"""
guards/page_guard.py — Evita flash de conteúdo errado em todas as páginas.

Uso em cada view:
    from guards.page_guard import page_guard

    @page_guard
    def show_voice():
        ...

    # ou sem decorator:
    def show_voice():
        with page_guard_context():
            ...
"""

import streamlit as st
from functools import wraps


# CSS que bloqueia qualquer flash visual durante carregamento
_LOADING_CSS = """
<style>
/* Esconde TODO conteúdo enquanto a classe pav-loading está no body */
body.pav-loading > * { visibility: hidden !important; }
body.pav-loading .stApp { background: #060a10 !important; }
</style>
"""

# JS que remove pav-loading assim que o DOM está pronto
_LOADING_JS = """
<script>
(function(){
    var doc = window.parent ? window.parent.document : document;
    doc.body.classList.add('pav-loading');
    function ready(){
        requestAnimationFrame(function(){
            doc.body.classList.remove('pav-loading');
        });
    }
    if(doc.readyState === 'complete') ready();
    else doc.addEventListener('DOMContentLoaded', ready);
    // Garantia: remove após 400ms no máximo
    setTimeout(function(){ doc.body.classList.remove('pav-loading'); }, 400);
})();
</script>
"""


def inject_anti_flash() -> None:
    """
    Injeta CSS + JS anti-flash no topo da página.
    Chame no início de cada view antes de renderizar qualquer coisa.
    """
    st.markdown(_LOADING_CSS, unsafe_allow_html=True)
    st.markdown(_LOADING_JS,  unsafe_allow_html=True)


def page_guard(func):
    """
    Decorator que:
    1. Injeta anti-flash antes de renderizar
    2. Bloqueia acesso se não estiver logado (redireciona para login)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        inject_anti_flash()

        if not st.session_state.get("logged_in"):
            st.session_state.page = "login"
            st.rerun()
            return

        return func(*args, **kwargs)
    return wrapper


def scroll_restore() -> None:
    """
    Restaura scroll nas páginas que precisam (history, settings, dashboard).
    Equivale ao bloco CSS que estava repetido em cada view.
    """
    st.markdown("""<style>
html, body { overflow: auto !important; }
section[data-testid="stMain"] > div,
.main .block-container { overflow: auto !important; max-height: none !important; }
div[data-testid="stVerticalBlock"],
div[data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="element-container"] { gap: revert !important; }
</style>""", unsafe_allow_html=True)
