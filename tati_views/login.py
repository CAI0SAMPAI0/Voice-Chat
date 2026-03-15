"""
tati_views/login.py — Recebe auth como parâmetro para não instanciar de novo.
"""

import streamlit as st
import streamlit.components.v1 as components

from database import authenticate, register_student, create_session
from ui_helpers import PROF_NAME, get_photo_b64, t, js_save_session
from guards.auth_helper import AuthHelper


def show_login(auth: AuthHelper) -> None:
    photo_src = get_photo_b64() or ""

    st.markdown("""<style>
[data-testid='stSidebar']{display:none!important;}
#MainMenu,footer,header,[data-testid="stToolbar"]{display:none!important;}
.stApp{background:#060a10!important;}
section[data-testid="stMain"],section[data-testid="stMain"]>div,.main .block-container{
    padding:0!important;margin:0!important;max-width:100%!important;width:100%!important;}
div[data-testid="stButton"]>button{
    border-radius:10px!important;font-weight:600!important;
    border:1px solid #2a2a4a!important;background:transparent!important;color:#6b7280!important;}
div[data-testid="stButton"]>button[kind="primary"]{
    background:linear-gradient(135deg,#6c3fc5,#8b5cf6)!important;
    border-color:#7c4dcc!important;color:#fff!important;
    box-shadow:0 0 14px rgba(139,92,246,.35)!important;}
div[data-testid="stFormSubmitButton"]>button{
    background:linear-gradient(135deg,#6c3fc5,#8b5cf6)!important;
    border:1px solid #7c4dcc!important;color:#fff!important;
    border-radius:10px!important;font-weight:700!important;}
section[data-testid="stMain"]>div>div>div{
    display:flex!important;flex-direction:column!important;align-items:center!important;}
div[data-testid="stVerticalBlock"]{
    width:100%!important;max-width:420px!important;margin:0 auto!important;padding:0 16px!important;}
</style>""", unsafe_allow_html=True)

    # ── Card visual ───────────────────────────────────────────────────────────
    if photo_src:
        av_html = (
            f'<img class="av" src="{photo_src}" alt="{PROF_NAME}" '
            f'onerror="this.style.display=\'none\';document.getElementById(\'avE\').style.display=\'flex\';">'
            f'<div class="av-emoji" id="avE" style="display:none">&#129489;&#8203;&#127979;</div>'
        )
    else:
        av_html = '<div class="av-emoji">&#129489;&#8203;&#127979;</div>'

    components.html(f"""<!DOCTYPE html><html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
html,body{{background:#060a10;font-family:'Sora',sans-serif;width:100%;height:100%;
    overflow:hidden;display:flex;align-items:center;justify-content:center;}}
.card{{background:linear-gradient(180deg,#0f1824,#0a1020);border:1px solid #1a2535;
    border-radius:24px;padding:28px 24px 20px;width:100%;
    box-shadow:0 24px 64px rgba(0,0,0,.7);display:flex;flex-direction:column;align-items:center;}}
.av{{width:90px;height:90px;border-radius:50%;object-fit:cover;object-position:top center;
    border:2.5px solid #8b5cf6;
    box-shadow:0 0 0 6px rgba(139,92,246,.12),0 0 28px rgba(139,92,246,.25);
    display:block;margin-bottom:12px;}}
.av-emoji{{width:90px;height:90px;border-radius:50%;
    background:linear-gradient(135deg,#6c3fc5,#8b5cf6);
    display:flex;align-items:center;justify-content:center;font-size:38px;margin-bottom:12px;}}
h2{{font-size:1.35rem;font-weight:800;text-align:center;margin:0 0 3px;
    background:linear-gradient(135deg,#8b5cf6 30%,#c084fc 100%);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
p{{font-size:.7rem;color:#3a4e5e;text-align:center;}}
</style></head><body>
<div class="card">{av_html}<h2>{PROF_NAME}</h2><p>Voice English Coach</p></div>
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
                if not u or not p:
                    st.session_state["_login_err"] = "Preencha todos os campos."; st.rerun()
                else:
                    user = authenticate(u, p)
                    if user:
                        real_u = user.get("_resolved_username", u.lower())
                        token  = create_session(real_u)
                        st.session_state.update(
                            logged_in=True,
                            user={"username": real_u, **user},
                            page="dashboard" if user["role"] == "professor" else "voice",
                            conv_id=None,
                        )
                        st.session_state["_session_token"] = token
                        st.session_state["_session_saved"] = True
                        auth.save(token)       # ← salva no cookie
                        js_save_session(token) # ← localStorage legado
                        st.rerun()
                    else:
                        st.session_state["_login_err"] = "Usuário ou senha incorretos."; st.rerun()

    # ── Form cadastro ─────────────────────────────────────────────────────────
    else:
        with st.form("form_reg", clear_on_submit=True):
            rn  = st.text_input(t("full_name"),  placeholder="João Silva")
            re_ = st.text_input(t("email"),      placeholder="joao@email.com")
            ru  = st.text_input(t("username"),   placeholder="joao.silva")
            rp  = st.text_input("Senha", type="password", placeholder="mínimo 6 caracteres")
            if st.form_submit_button(t("create_account"), use_container_width=True):
                if not rn or not re_ or not ru or not rp:
                    st.session_state["_reg_err"] = "Preencha todos os campos."; st.rerun()
                elif "@" not in re_:
                    st.session_state["_reg_err"] = "E-mail inválido."; st.rerun()
                elif len(rp) < 6:
                    st.session_state["_reg_err"] = "Senha muito curta (mínimo 6)."; st.rerun()
                else:
                    ok, msg = register_student(ru, rn, rp, email=re_)
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