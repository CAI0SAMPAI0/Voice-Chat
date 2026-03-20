"""
asset_loader.py — Carrega CSS, JS e HTML de arquivos em assets/
Centraliza toda injeção de recursos no Streamlit.

Uso:
    from asset_loader import css, js, html, inject_css, inject_js

    inject_css("global")           # injeta <style> do global.css
    inject_css("global", "voice")  # injeta múltiplos de uma vez
    inject_js("session", token=token_value)  # com substituição de variáveis
    card = html("avatar_card", name="Tati", status="Online")
"""

from pathlib import Path
import streamlit as st

_BASE = Path(__file__).resolve().parent / "assets"


# ── Leitura raw ───────────────────────────────────────────────────────────────

def css(name: str) -> str:
    """Retorna o conteúdo de assets/css/{name}.css como string.
    Lê do disco a cada chamada — sem cache — para refletir edições imediatas.
    """
    path = _BASE / "css" / f"{name}.css"
    if not path.exists():
        return f"/* ⚠️ assets/css/{name}.css não encontrado */"
    # mtime como comentário força o browser a tratar como bloco diferente
    mtime = int(path.stat().st_mtime)
    return f"/* {name} v{mtime} */\n" + path.read_text(encoding="utf-8")


def js(name: str, **vars: str) -> str:
    """Retorna o conteúdo de assets/js/{name}.js como string.
    Substitui {{VAR_NAME}} pelas variáveis passadas como kwargs.
    """
    path = _BASE / "js" / f"{name}.js"
    if not path.exists():
        return f"// ⚠️ assets/js/{name}.js não encontrado"
    content = path.read_text(encoding="utf-8")
    for key, val in vars.items():
        content = content.replace(f"{{{{{key}}}}}", str(val))
    return content


def html(name: str, **vars: str) -> str:
    """Retorna o conteúdo de assets/html/{name}.html como string.
    Substitui {{VAR_NAME}} pelas variáveis passadas como kwargs.
    """
    path = _BASE / "html" / f"{name}.html"
    if not path.exists():
        return f"<!-- ⚠️ assets/html/{name}.html não encontrado -->"
    content = path.read_text(encoding="utf-8")
    for key, val in vars.items():
        content = content.replace(f"{{{{{key}}}}}", str(val))
    return content


# ── Injeção no Streamlit ──────────────────────────────────────────────────────

def inject_css(*names: str) -> None:
    """Injeta um ou mais arquivos CSS no Streamlit via st.markdown.

    Cada arquivo é lido do disco na hora — sem cache de módulo.
    O comentário com mtime no topo de cada bloco garante que o browser
    aplique a versão mais recente mesmo sem hard-refresh.
    """
    combined = "\n".join(css(name) for name in names)
    st.markdown(f"<style>{combined}</style>", unsafe_allow_html=True)


def inject_js(*names: str, **vars: str) -> None:
    """Injeta um ou mais arquivos JS no Streamlit via st.markdown."""
    combined = "\n".join(js(name, **vars) for name in names)
    st.markdown(f"<script>{combined}</script>", unsafe_allow_html=True)


def inject_html(name: str, **vars: str) -> None:
    """Injeta um arquivo HTML no Streamlit via st.markdown."""
    st.markdown(html(name, **vars), unsafe_allow_html=True)


def inject_component(name: str, height: int = 0, **vars: str) -> None:
    """Injeta um arquivo HTML como components.html.
    Útil para JS que precisa acessar window.parent ou manipular o DOM.
    """
    import streamlit.components.v1 as components
    components.html(html(name, **vars), height=height)