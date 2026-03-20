"""
guards/page_guard.py — Anti-flash + autenticação + scroll por página.

Mudanças vs versão anterior:
─────────────────────────────
1. scroll_restore() era GLOBAL: afetava stVerticalBlock em todo o DOM,
   incluindo os botões da sidebar (mudava gap e espaçamento dos itens
   de nav dependendo da página ativa). Corrigido: agora restringe os
   overrides ao conteúdo principal via seletor
   `section[data-testid="stMain"]`, nunca tocando na sidebar.

2. Adicionado comentário explicando por que cada seletor existe —
   para o próximo dev não "consertar" e reintroduzir o bug.
"""

import streamlit as st
from functools import wraps


# CSS anti-flash: esconde tudo enquanto a página carrega
_LOADING_CSS = """
<style>
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
    2. Redireciona para login se não estiver autenticado
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

    POR QUE EXISTE:
    voice.css define overflow: hidden globalmente (necessário para a tela
    de voz não ter scroll). Ao navegar para history/settings/dashboard,
    esse CSS ainda está no DOM (Streamlit não limpa estilos entre reruns).
    Esta função sobrescreve apenas o necessário para a página atual rolar.

    POR QUE O ESCOPO É RESTRITO A stMain:
    A versão anterior usava seletores globais como:
        div[data-testid="stVerticalBlock"] { gap: revert !important; }
    Isso afetava os botões da sidebar — que também são stVerticalBlock —
    mudando o espaçamento dos itens de nav dependendo de qual página
    estava ativa. O resultado eram sidebar com aparência diferente em
    cada tela.

    Solução: todos os overrides agora vivem dentro de
    `section[data-testid="stMain"]`, que é o container do conteúdo
    principal e nunca inclui a sidebar.
    """
    st.markdown("""<style>
/* Restaura scroll APENAS no conteúdo principal */
section[data-testid="stMain"] {
    overflow-y: auto !important;
}
section[data-testid="stMain"] > div,
.main .block-container {
    overflow:   auto !important;
    max-height: none !important;
    height:     auto !important;
}

/*
 * Restaura gap dos blocos verticais APENAS dentro do main.
 * NÃO usa seletor global para não afetar a sidebar.
 */
section[data-testid="stMain"] div[data-testid="stVerticalBlock"],
section[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"],
section[data-testid="stMain"] div[data-testid="element-container"] {
    gap:        revert !important;
    height:     auto   !important;
    max-height: none   !important;
    overflow:   visible !important;
}

/* Restaura html/body para permitir scroll de página */
html, body { overflow-y: auto !important; }
</style>""", unsafe_allow_html=True)