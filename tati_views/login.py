"""
tati_views/login.py — Recebe auth como parâmetro para não instanciar de novo.
"""

from datetime import datetime, timedelta

import streamlit as st
import streamlit.components.v1 as components

from database import authenticate, register_student, create_session
from ui_helpers import PROF_NAME, get_photo_b64, t, js_save_session
from guards.auth_helper import AuthHelper


def _is_rate_limited() -> tuple[bool, str | None]:
    """Limita tentativas de login por sessão."""
    max_attempts = 5
    block_secs   = 60

    attempts = st.session_state.get("_login_attempts", 0)
    blocked_until = st.session_state.get("_login_block_until")

    now = datetime.utcnow().timestamp()
    if blocked_until and now < blocked_until:
        remaining = int(blocked_until - now)
        return True, f"Muitas tentativas. Aguarde {remaining}s para tentar novamente."

    if attempts >= max_attempts:
        st.session_state["_login_block_until"] = now + block_secs
        st.session_state["_login_attempts"] = 0
        return True, f"Muitas tentativas. Aguarde {block_secs}s para tentar novamente."

    return False, None


def _register_failed_attempt() -> None:
    st.session_state["_login_attempts"] = st.session_state.get("_login_attempts", 0) + 1


def show_login(auth: AuthHelper) -> None:
    photo_src = get_photo_b64() or ""

    # CSS externo de login
    from asset_loader import inject_css
    inject_css("login")

    # ── Libera scroll na tela de login ──────────────────────────────────────────
    # Deve vir DEPOIS do inject_css para sobrescrever global.css e login.css
    st.markdown("""<style>
/* Desfaz o height: -webkit-fill-available do global.css */
html {
    height: auto !important;
    min-height: 100% !important;
    overflow-y: scroll !important;
    overflow-x: hidden !important;
}
/* Desfaz o min-height: 100vh travado do global.css */
body {
    height: auto !important;
    min-height: 100% !important;
    overflow-y: scroll !important;
    overflow-x: hidden !important;
    background: #060a10 !important;
}
/* stApp e containers principais */
.stApp,
[data-testid="stAppViewContainer"] {
    height: auto !important;
    min-height: 100vh !important;
    overflow: visible !important;
}
/* stMain é quem realmente corta o conteúdo */
section[data-testid="stMain"],
section[data-testid="stMain"] > div {
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
    overflow: visible !important;
}
/* block-container: espaço interno do formulário */
.main .block-container {
    height: auto !important;
    max-height: none !important;
    overflow: visible !important;
    padding-top: 1rem !important;
    padding-bottom: 100px !important;
}
/* Todos os blocos verticais do Streamlit */
div[data-testid="stVerticalBlock"],
div[data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="element-container"],
div[data-testid="stFormSubmitButton"] {
    overflow: visible !important;
    height: auto !important;
    max-height: none !important;
}
</style>""", unsafe_allow_html=True)

    # ── Card visual ───────────────────────────────────────────────────────────
    # A foto é renderizada como background de um div circular (não como <img>)
    # para garantir que o círculo funcione corretamente em todos os navegadores.
    if photo_src:
        av_html = f"""
<div style="
    width: 90px;
    height: 90px;
    border-radius: 50%;
    background-image: url('{photo_src}');
    background-size: cover;
    background-position: top center;
    border: 2.5px solid #8b5cf6;
    box-shadow: 0 0 0 6px rgba(139,92,246,0.12), 0 0 28px rgba(139,92,246,0.25);
    margin-bottom: 12px;
    flex-shrink: 0;
"></div>"""
    else:
        av_html = """
<div style="
    width: 90px;
    height: 90px;
    border-radius: 50%;
    background: linear-gradient(135deg, #6c3fc5, #8b5cf6);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 38px;
    margin-bottom: 12px;
">&#129489;&#8203;&#127979;</div>"""

    components.html(f"""<!DOCTYPE html><html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,maximum-scale=1.0,user-scalable=no">
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
html,body{{
    background:#060a10;
    font-family:'Sora',sans-serif;
    width:100%;height:100%;
    overflow:hidden;
    display:flex;align-items:center;justify-content:center;
}}
.login-card{{
    background:linear-gradient(180deg,#0f1824,#0a1020);
    border:1px solid #1a2535;
    border-radius:24px;
    padding:28px 24px 20px;
    width:100%;
    box-shadow:0 24px 64px rgba(0,0,0,.7);
    display:flex;flex-direction:column;align-items:center;
}}
.login-title{{
    font-size:1.35rem;font-weight:800;text-align:center;margin:0 0 3px;
    background:linear-gradient(135deg,#8b5cf6 30%,#c084fc 100%);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
}}
.login-subtitle{{font-size:.7rem;color:#3a4e5e;text-align:center;}}
</style></head><body>
<div class="login-card">
    {av_html}
    <h2 class="login-title">{PROF_NAME}</h2>
    <p class="login-subtitle">Voice English Coach</p>
</div>
</body></html>""", height=220, scrolling=False)

    # ── Feedback ──────────────────────────────────────────────────────────────
    login_err = st.session_state.pop("_login_err", "")
    reg_err   = st.session_state.pop("_reg_err",   "")
    reg_ok    = st.session_state.pop("_reg_ok",    False)
    reg_name  = st.session_state.pop("_reg_name",  "")
    if login_err: st.error(f"❌ {login_err}")
    if reg_err:   st.error(f"❌ {reg_err}")
    if reg_ok:    st.success(f"✅ Conta criada! Bem-vindo(a), {reg_name}!")

    # ── Abas ──────────────────────────────────────────────────────────────────
    if "_login_tab" not in st.session_state:
        st.session_state["_login_tab"] = "login"
    tab = st.session_state["_login_tab"]

    c1, c2 = st.columns(2)
    with c1:
        if st.button(t("enter"), use_container_width=True, key="tab_login",
                     type="primary" if tab == "login" else "secondary"):
            st.session_state["_login_tab"] = "login"; st.rerun()
    with c2:
        if st.button(t("create_account"), use_container_width=True, key="tab_reg",
                     type="primary" if tab == "reg" else "secondary"):
            st.session_state["_login_tab"] = "reg"; st.rerun()

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── Form login ────────────────────────────────────────────────────────────
    if tab == "login":
        with st.form("form_login", clear_on_submit=True):
            u = st.text_input(t("username"), placeholder="seu.usuario")
            p = st.text_input(t("password"), type="password", placeholder="••••••••")
            if st.form_submit_button(t("enter"), use_container_width=True):
                limited, msg = _is_rate_limited()
                if limited:
                    st.session_state["_login_err"] = msg or "Muitas tentativas. Tente novamente em instantes."
                    st.rerun()
                elif not u or not p:
                    st.session_state["_login_err"] = "Preencha todos os campos."
                    st.rerun()
                else:
                    user = authenticate(u, p)
                    if user:
                        # Reset contador em login bem-sucedido
                        st.session_state["_login_attempts"] = 0
                        st.session_state["_login_block_until"] = None

                        real_u = user.get("_resolved_username", u.lower())
                        token  = create_session(real_u)
                        page   = "dashboard" if user["role"] in ("professor", "programador") else "voice"
                        st.session_state.update(
                            logged_in=True,
                            user={"username": real_u, **user},
                            page=page,
                            conv_id=None,
                        )
                        st.session_state["_session_token"] = token
                        st.session_state["_session_saved"] = True
                        auth.save(token)       # ← salva no cookie
                        js_save_session(token) # ← localStorage legado
                        st.rerun()
                    else:
                        _register_failed_attempt()
                        st.session_state["_login_err"] = "Usuário ou senha incorretos."
                        st.rerun()

    # ── Form cadastro ─────────────────────────────────────────────────────────
    else:
        with st.form("form_reg", clear_on_submit=True):
            rn  = st.text_input(t("full_name"),  placeholder="João Silva")
            re_ = st.text_input(t("email"),      placeholder="joao@email.com")
            ru  = st.text_input(t("username"),   placeholder="joao.silva")
            rp  = st.text_input("Senha", type="password", placeholder="mínimo 6 caracteres")
            level_opts = ["Beginner","Pre-Intermediate","Intermediate","Advanced","Business English"]
            level = st.selectbox("Nível de inglês", level_opts, index=0)
            birth = st.date_input("Data de nascimento", format="DD/MM/YYYY")
            if st.form_submit_button(t("create_account"), use_container_width=True):
                if not rn or not re_ or not ru or not rp:
                    st.session_state["_reg_err"] = "Preencha todos os campos."; st.rerun()
                elif "@" not in re_:
                    st.session_state["_reg_err"] = "E-mail inválido."; st.rerun()
                elif len(rp) < 6:
                    st.session_state["_reg_err"] = "Senha muito curta (mínimo 6)."; st.rerun()
                else:
                    birth_str = birth.isoformat() if birth else ""
                    ok, msg = register_student(ru, rn, rp, email=re_, level=level, focus="General Conversation")
                    if ok:
                        from database import update_profile
                        update_profile(ru, {"birthdate": birth_str})
                    if ok:
                        st.session_state["_reg_ok"]    = True
                        st.session_state["_reg_name"]  = rn
                        st.session_state["_login_tab"] = "login"
                        st.rerun()
                    else:
                        st.session_state["_reg_err"] = msg; st.rerun()

    st.markdown(
        f'<p style="text-align:center;font-size:.6rem;color:#1a2535;margin-top:14px;">'
        f'2025 © {PROF_NAME}</p>',
        unsafe_allow_html=True,
    )