"""
pages/login.py — Tela de login / cadastro.
"""

import streamlit as st
import streamlit.components.v1 as components

from database import authenticate, register_student, create_session
from ui_helpers import PROF_NAME, get_photo_b64, t, js_save_session


def show_login() -> None:
    photo_src = get_photo_b64()

    # Auto-login via localStorage/cookie
    components.html("""<!DOCTYPE html><html><head>
<style>html,body{margin:0;padding:0;overflow:hidden;}</style>
</head><body><script>
(function(){
    function readToken(){
        try{var s=window.parent.localStorage.getItem('pav_session');if(s&&s.length>10)return s;}catch(e){}
        try{var s2=localStorage.getItem('pav_session');if(s2&&s2.length>10)return s2;}catch(e){}
        try{var m=window.parent.document.cookie.split(';').map(function(c){return c.trim();})
            .find(function(c){return c.startsWith('pav_session=');});
            if(m){var v=decodeURIComponent(m.split('=')[1]);if(v&&v.length>10)return v;}}catch(e){}
        return '';
    }
    var val=readToken();
    if(!val)return;
    var url=new URL(window.parent.location.href);
    if(url.searchParams.get('s')!==val){
        url.searchParams.set('s',val);
        window.parent.location.replace(url.toString());
    }
})();
</script></body></html>""", height=1)

    st.markdown("<style>[data-testid='stSidebar']{display:none!important;}</style>",
                unsafe_allow_html=True)

    if "_login_tab" not in st.session_state:
        st.session_state["_login_tab"] = "login"

    _, col, _ = st.columns([1, 1.8, 1])
    with col:
        # Header visual
        components.html(f"""<!DOCTYPE html><html><head>
<meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
html,body{{background:#060a10;font-family:'Sora',sans-serif;overflow:hidden;}}
.wrap{{display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px;}}
.card{{background:linear-gradient(180deg,#0f1824,#0a1020);border:1px solid #1a2535;
       border-radius:24px;padding:32px 28px 24px;width:100%;max-width:400px;
       box-shadow:0 32px 80px rgba(0,0,0,.6);}}
.av{{width:84px;height:84px;border-radius:50%;object-fit:cover;object-position:top;
     display:block;margin:0 auto 14px;
     border:2.5px solid #f0a500;
     box-shadow:0 0 0 6px rgba(240,165,0,.1),0 0 32px rgba(240,165,0,.2);}}
.av-emoji{{width:84px;height:84px;border-radius:50%;
           background:linear-gradient(135deg,#f0a500,#e05c2a);
           display:flex;align-items:center;justify-content:center;
           font-size:38px;margin:0 auto 14px;}}
h2{{font-size:1.4rem;font-weight:800;text-align:center;margin:0 0 4px;
    background:linear-gradient(135deg,#f0a500 30%,#e05c2a 100%);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
p{{font-size:.72rem;color:#3a4e5e;text-align:center;}}
</style></head><body>
<div class="wrap"><div class="card">
    {"<img class='av' src='" + photo_src + "'/>" if photo_src else "<div class='av-emoji'>&#129489;&#8205;&#127979;</div>"}
    <h2>{PROF_NAME}</h2>
    <p>Voice English Coach</p>
</div></div>
</body></html>""", height=260, scrolling=False)

        c1, c2 = st.columns(2)
        with c1:
            if st.button(t("enter"), use_container_width=True, key="tab_login",
                         type="primary" if st.session_state["_login_tab"] == "login" else "secondary"):
                st.session_state["_login_tab"] = "login"; st.rerun()
        with c2:
            if st.button(t("create_account"), use_container_width=True, key="tab_reg",
                         type="primary" if st.session_state["_login_tab"] == "reg" else "secondary"):
                st.session_state["_login_tab"] = "reg"; st.rerun()

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        login_err = st.session_state.pop("_login_err", "")
        reg_err   = st.session_state.pop("_reg_err",   "")
        reg_ok    = st.session_state.pop("_reg_ok",    False)
        reg_name  = st.session_state.pop("_reg_name",  "")
        if login_err: st.error(f"❌ {login_err}")
        if reg_err:   st.error(f"❌ {reg_err}")
        if reg_ok:    st.success(f"✅ Conta criada! Bem-vindo(a), {reg_name}!")

        if st.session_state["_login_tab"] == "login":
            with st.form("form_login", clear_on_submit=True):
                u = st.text_input(t("username"), placeholder="seu.usuario")
                p = st.text_input(t("password"), type="password", placeholder="••••••••")
                if st.form_submit_button(t("enter"), use_container_width=True):
                    if not u or not p:
                        st.session_state["_login_err"] = "Preencha todos os campos."
                        st.rerun()
                    else:
                        user = authenticate(u, p)
                        if user:
                            real_u = user.get("_resolved_username", u.lower())
                            st.session_state.update(
                                logged_in=True,
                                user={"username": real_u, **user},
                                page="dashboard" if user["role"] == "professor" else "voice",
                                conv_id=None,
                            )
                            token = create_session(real_u)
                            st.session_state["_session_token"] = token
                            st.session_state["_session_saved"] = True
                            js_save_session(token)
                            st.rerun()
                        else:
                            st.session_state["_login_err"] = "Usuário ou senha incorretos."
                            st.rerun()
        else:
            with st.form("form_reg", clear_on_submit=True):
                rn  = st.text_input(t("full_name"),  placeholder="João Silva")
                re_ = st.text_input(t("email"),      placeholder="joao@email.com")
                ru  = st.text_input(t("username"),   placeholder="joao.silva")
                rp  = st.text_input("Senha", type="password", placeholder="mínimo 6 caracteres")
                if st.form_submit_button(t("create_account"), use_container_width=True):
                    if not rn or not re_ or not ru or not rp:
                        st.session_state["_reg_err"] = "Preencha todos os campos."
                        st.rerun()
                    elif "@" not in re_:
                        st.session_state["_reg_err"] = "E-mail inválido."
                        st.rerun()
                    elif len(rp) < 6:
                        st.session_state["_reg_err"] = "Senha muito curta (mínimo 6)."
                        st.rerun()
                    else:
                        ok, msg = register_student(ru, rn, rp, email=re_)
                        if ok:
                            st.session_state["_reg_ok"]    = True
                            st.session_state["_reg_name"]  = rn
                            st.session_state["_login_tab"] = "login"
                            st.rerun()
                        else:
                            st.session_state["_reg_err"] = msg
                            st.rerun()

        st.markdown(
            f'<p style="text-align:center;font-size:.6rem;color:#1a2535;margin-top:14px;">'
            f'2025 © {PROF_NAME}</p>',
            unsafe_allow_html=True)
