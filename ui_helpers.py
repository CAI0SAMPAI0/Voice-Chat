"""
ui_helpers.py — Utilitários de UI compartilhados entre todas as páginas.
Centraliza: avatares, i18n, CSS global, sidebar, helpers de sessão.
"""

import os
import base64
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from database import (
    delete_session,
    new_conversation,
    get_user_avatar_db,
    save_user_avatar_db,
    remove_user_avatar_db,
)

# =============================================================================
# CONSTANTES
# =============================================================================
PROF_NAME  = os.getenv("PROFESSOR_NAME", "Teacher Tati")
PHOTO_PATH = os.getenv("PROFESSOR_PHOTO", "assets/professor.jpg")

# =============================================================================
# I18N
# =============================================================================
_STRINGS = {
    "pt-BR": {
        "username":           "Usuário",
        "password":           "Senha",
        "enter":              "Entrar",
        "create_account":     "Criar Conta",
        "full_name":          "Nome completo",
        "email":              "E-mail",
        "logout":             "Sair",
        "settings":           "Configurações",
        "history":            "Histórico",
        "dashboard":          "Painel",
        "voice_mode":         "Modo Voz",
        "new_conv":           "Nova conversa de voz",
        "del_conv":           "Excluir",
        "tap_to_speak":       "Toque para falar",
        "tap_to_stop":        "Toque para parar",
        "processing":         "Processando...",
        "speaking_ai":        "Falando...",
        "save":               "Salvar",
        "english_level":      "Nível de inglês",
        "focus":              "Foco",
        "interface_lang":     "Idioma da interface",
        "voice_lang":         "Sotaque da IA (voz)",
        "change_password":    "Alterar senha",
        "new_password":       "Nova senha",
        "confirm_password":   "Confirmar senha",
        "cancel":             "Cancelar",
        "students":           "Alunos",
        "total_msgs":         "Mensagens",
        "conversations":      "Conversas",
        "last_activity":      "Última atividade",
        "no_history":         "Nenhuma conversa ainda.",
        "error_api":          "Erro ao chamar a IA.",
        "error_mic":          "Erro no microfone.",
        "section_photo":      "📸 Foto de Perfil",
        "photo_upload_label": "Alterar foto — JPG, PNG ou WEBP (máx 15 MB)",
        "photo_remove":       "🗑️ Remover foto",
        "photo_saved":        "✅ Foto salva!",
        "photo_removed":      "Foto removida.",
        "photo_too_large":    "❌ Foto muito grande. Máximo 15 MB.",
        "section_personal":   "👤 Informações da Conta",
        "username_label":     "Usuário",
        "section_password":   "🔒 Alterar Senha",
        "pwd_fill_both":      "Preencha os dois campos.",
        "pwd_mismatch":       "As senhas não coincidem.",
        "pwd_too_short":      "Mínimo 6 caracteres.",
        "pwd_changed":        "✅ Senha alterada!",
        "pwd_error":          "Erro ao alterar senha.",
        "data_saved":         "✅ Dados atualizados!",
        "save_error":         "Erro ao salvar.",
        "section_learning":   "🎓 Perfil de Aprendizado",
        "section_lang":       "🌐 Idioma da Interface",
        "reload_lang":        "Salvo! Recarregue para ver o novo idioma.",
        "section_appearance": "🎨 Aparência",
        "ring_color":         "Cor do anel",
        "user_bubble_color":  "Sua bolha",
        "bot_bubble_color":   "Bolha da IA",
        "appearance_hint":    "As cores aparecem imediatamente no modo conversa.",
    },
    "en-US": {
        "username":           "Username",
        "password":           "Password",
        "enter":              "Sign In",
        "create_account":     "Create Account",
        "full_name":          "Full name",
        "email":              "E-mail",
        "logout":             "Log out",
        "settings":           "Settings",
        "history":            "History",
        "dashboard":          "Dashboard",
        "voice_mode":         "Voice Mode",
        "new_conv":           "New voice chat",
        "del_conv":           "Delete",
        "tap_to_speak":       "Tap to speak",
        "tap_to_stop":        "Tap to stop",
        "processing":         "Processing...",
        "speaking_ai":        "Speaking...",
        "save":               "Save",
        "english_level":      "English level",
        "focus":              "Focus",
        "interface_lang":     "Interface language",
        "voice_lang":         "AI voice accent",
        "change_password":    "Change password",
        "new_password":       "New password",
        "confirm_password":   "Confirm password",
        "cancel":             "Cancel",
        "students":           "Students",
        "total_msgs":         "Messages",
        "conversations":      "Conversations",
        "last_activity":      "Last activity",
        "no_history":         "No conversations yet.",
        "error_api":          "Error calling AI.",
        "error_mic":          "Microphone error.",
        "section_photo":      "📸 Profile Photo",
        "photo_upload_label": "Change photo — JPG, PNG or WEBP (max 15 MB)",
        "photo_remove":       "🗑️ Remove photo",
        "photo_saved":        "✅ Photo saved!",
        "photo_removed":      "Photo removed.",
        "photo_too_large":    "❌ Photo too large. Maximum 15 MB.",
        "section_personal":   "👤 Account Information",
        "username_label":     "Username",
        "section_password":   "🔒 Change Password",
        "pwd_fill_both":      "Please fill in both fields.",
        "pwd_mismatch":       "Passwords do not match.",
        "pwd_too_short":      "Minimum 6 characters.",
        "pwd_changed":        "✅ Password changed!",
        "pwd_error":          "Error changing password.",
        "data_saved":         "✅ Data updated!",
        "save_error":         "Error saving.",
        "section_learning":   "🎓 Learning Profile",
        "section_lang":       "🌐 Interface Language",
        "reload_lang":        "Saved! Reload to see the new language.",
        "section_appearance": "🎨 Appearance",
        "ring_color":         "Ring colour",
        "user_bubble_color":  "Your bubble",
        "bot_bubble_color":   "AI bubble",
        "appearance_hint":    "Colours apply instantly in conversation mode.",
    },
    "en-UK": {
        "username":           "Username",
        "password":           "Password",
        "enter":              "Sign In",
        "create_account":     "Create Account",
        "full_name":          "Full name",
        "email":              "E-mail",
        "logout":             "Log out",
        "settings":           "Settings",
        "history":            "History",
        "dashboard":          "Dashboard",
        "voice_mode":         "Voice Mode",
        "new_conv":           "New voice chat",
        "del_conv":           "Delete",
        "tap_to_speak":       "Tap to speak",
        "tap_to_stop":        "Tap to stop",
        "processing":         "Processing...",
        "speaking_ai":        "Speaking...",
        "save":               "Save",
        "english_level":      "English level",
        "focus":              "Focus",
        "interface_lang":     "Interface language",
        "voice_lang":         "AI voice accent",
        "change_password":    "Change password",
        "new_password":       "New password",
        "confirm_password":   "Confirm password",
        "cancel":             "Cancel",
        "students":           "Students",
        "total_msgs":         "Messages",
        "conversations":      "Conversations",
        "last_activity":      "Last activity",
        "no_history":         "No conversations yet.",
        "error_api":          "Error calling AI.",
        "error_mic":          "Microphone error.",
        "section_photo":      "📸 Profile Photo",
        "photo_upload_label": "Change photo — JPG, PNG or WEBP (max 15 MB)",
        "photo_remove":       "🗑️ Remove photo",
        "photo_saved":        "✅ Photo saved!",
        "photo_removed":      "Photo removed.",
        "photo_too_large":    "❌ Photo too large. Maximum 15 MB.",
        "section_personal":   "👤 Account Information",
        "username_label":     "Username",
        "section_password":   "🔒 Change Password",
        "pwd_fill_both":      "Please fill in both fields.",
        "pwd_mismatch":       "Passwords do not match.",
        "pwd_too_short":      "Minimum 6 characters.",
        "pwd_changed":        "✅ Password changed!",
        "pwd_error":          "Error changing password.",
        "data_saved":         "✅ Data updated!",
        "save_error":         "Error saving.",
        "section_learning":   "🎓 Learning Profile",
        "section_lang":       "🌐 Interface Language",
        "reload_lang":        "Saved! Reload to see the new language.",
        "section_appearance": "🎨 Appearance",
        "ring_color":         "Ring colour",
        "user_bubble_color":  "Your bubble",
        "bot_bubble_color":   "AI bubble",
        "appearance_hint":    "Colours apply instantly in conversation mode.",
    },
}

def t(key: str, lang: str = "pt-BR", default: str = None) -> str:
    val = _STRINGS.get(lang, _STRINGS["pt-BR"]).get(key)
    if val is not None:
        return val
    val = _STRINGS["pt-BR"].get(key)
    if val is not None:
        return val
    return default if default is not None else key


# =============================================================================
# FOTO / AVATAR
# =============================================================================

def get_photo_b64() -> str | None:
    p = Path(PHOTO_PATH)
    if p.exists():
        ext  = p.suffix.lower().replace(".", "")
        mime = "jpeg" if ext in ("jpg", "jpeg") else ext
        return f"data:image/{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"
    return None


def get_tati_mini_b64() -> str:
    for _p in [Path("assets/tati.png"), Path("assets/tati.jpg")]:
        if _p.exists():
            _ext  = _p.suffix.lstrip(".").lower()
            _mime = "jpeg" if _ext in ("jpg", "jpeg") else _ext
            return f"data:image/{_mime};base64,{base64.b64encode(_p.read_bytes()).decode()}"
    return get_photo_b64() or ""


def get_avatar_frames() -> dict:
    import os
    _base = Path(__file__).resolve().parent
    _cwd  = Path(os.getcwd()).resolve()

    def _load(filename: str) -> str:
        """Tenta carregar filename a partir de múltiplas bases."""
        for base in [_cwd, _base, _cwd.parent, _base.parent]:
            p = base / "assets" / filename
            if p.exists():
                return f"data:image/png;base64,{base64.b64encode(p.read_bytes()).decode()}"
        return ""

    return {
        "normal":     _load("avatar_tati_normal.png"),
        "meio":       _load("avatar_tati_meio.png"),
        "aberta":     _load("avatar_tati_aberta.png"),
        "bem_aberta": _load("avatar_tati_bem_aberta.png"),
        "ouvindo":    _load("avatar_tati_ouvindo.png"),
        "piscando":   _load("tati_piscando.png"),
        "surpresa":   _load("tati_surpresa.png"),
    }


def _get_avatar(username: str) -> str | None:
    result = get_user_avatar_db(username)
    if not result:
        return None
    raw, mime = result
    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"


def get_user_avatar_b64(username: str) -> str | None:
    return _get_avatar(username)


def save_user_avatar(username: str, raw: bytes, suffix: str) -> None:
    suffix = suffix.lower().lstrip(".")
    mime   = "image/jpeg" if suffix in ("jpg", "jpeg") else f"image/{suffix}"
    save_user_avatar_db(username, raw, mime)


def remove_user_avatar(username: str) -> None:
    remove_user_avatar_db(username)


def _avatar_circle_html(b64: str | None, size: int, border: str = "#f0a500") -> str:
    if not b64:
        for _p in [Path("assets/sem_foto.png"), Path(__file__).parent / "assets" / "sem_foto.png"]:
            if _p.exists():
                b64 = f"data:image/png;base64,{base64.b64encode(_p.read_bytes()).decode()}"
                break
    if b64:
        return (
            f'<div style="width:{size}px;height:{size}px;border-radius:50%;'
            f'background:url({b64}) center/cover no-repeat;'
            f'border:2px solid {border};flex-shrink:0;"></div>'
        )
    icon_px = int(size * 0.50)
    return (
        f'<div style="width:{size}px;height:{size}px;border-radius:50%;'
        f'background:linear-gradient(135deg,#1e2a3a,#2a3a50);'
        f'display:flex;align-items:center;justify-content:center;'
        f'border:2px solid #1e2a3a;flex-shrink:0;">'
        f'<i class="fa-duotone fa-solid fa-user-graduate" '
        f'style="font-size:{icon_px}px;'
        f'--fa-primary-color:#f0a500;--fa-secondary-color:#c87800;'
        f'--fa-secondary-opacity:0.6;"></i>'
        f'</div>'
    )


def user_avatar_html(username: str, size: int = 36, **_) -> str:
    return _avatar_circle_html(_get_avatar(username), size)


# =============================================================================
# SESSION DEFAULTS
# =============================================================================
SESSION_DEFAULTS = {
    "logged_in":       False,
    "user":            None,
    "page":            "voice",
    "conv_id":         None,
    "audio_key":       0,
    "_vm_history":     [],
    "_vm_reply":       "",
    "_vm_tts_b64":     "",
    "_vm_user_said":   "",
    "_vm_error":       "",
    "_vm_last_upload": None,
}

def init_session():
    for k, v in SESSION_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _logout():
    token = st.session_state.get("_session_token", "")
    if token:
        delete_session(token)
    components.html("""<!DOCTYPE html><html><head>
<style>html,body{margin:0;padding:0;overflow:hidden;}</style>
</head><body><script>
(function(){
    try{window.parent.localStorage.removeItem('pav_session');}catch(e){}
    try{localStorage.removeItem('pav_session');}catch(e){}
    try{window.parent.document.cookie='pav_session=;expires=Thu,01 Jan 1970 00:00:00 GMT;path=/';}catch(e){}
    try{document.cookie='pav_session=;expires=Thu,01 Jan 1970 00:00:00 GMT;path=/';}catch(e){}
})();
</script></body></html>""", height=1)
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    for k, v in SESSION_DEFAULTS.items():
        st.session_state[k] = v
    st.session_state.pop("_session_saved", None)


def js_save_session(token: str) -> None:
    components.html(f"""<!DOCTYPE html><html><head>
<style>html,body{{margin:0;padding:0;overflow:hidden;}}</style>
</head><body><script>
(function(){{
    var t='{token}';
    try{{window.parent.localStorage.setItem('pav_session',t);}}catch(e){{}}
    try{{localStorage.setItem('pav_session',t);}}catch(e){{}}
    try{{
        var exp=new Date(Date.now()+2592000000).toUTCString();
        window.parent.document.cookie='pav_session='+encodeURIComponent(t)+';expires='+exp+';path=/;SameSite=Lax';
    }}catch(e){{}}
}})();
</script></body></html>""", height=1)


def get_or_create_conv(username: str) -> str:
    from database import list_conversations, new_conversation as _new
    if st.session_state.conv_id:
        return st.session_state.conv_id
    convs = list_conversations(username)
    cid = convs[0]["id"] if convs else _new(username)
    st.session_state.conv_id = cid
    return cid


# =============================================================================
# CSS GLOBAL
# =============================================================================
_SB_W = 260   # sidebar width px

def inject_global_css():
    st.markdown(f"""<style>
/* ── Reset Streamlit ── */
#MainMenu, footer, header {{ display: none !important; }}
[data-testid="stToolbar"] {{ display: none !important; }}
section[data-testid="stMain"] > div {{ max-width: 100% !important; padding: 0 !important; }}
.main .block-container {{ max-width: 100% !important; padding: 0 !important; }}
html {{ height: -webkit-fill-available; }}
body {{ min-height: 100vh; min-height: -webkit-fill-available; }}
.stApp {{ min-height: 100vh; min-height: -webkit-fill-available; }}

/* ── Sidebar fixa ── */
section[data-testid="stSidebar"] {{
    background: #070c15 !important;
    border-right: 1px solid #1a2535 !important;
    width: {_SB_W}px !important; min-width: {_SB_W}px !important; max-width: {_SB_W}px !important;
    position: fixed !important; top: 0 !important; left: 0 !important; bottom: 0 !important;
    z-index: 2000 !important;
    transition: transform 0.28s cubic-bezier(.4,0,.2,1) !important;
    transform: translateX(0) !important;
    overflow-y: auto !important; overflow-x: hidden !important;
}}
section[data-testid="stSidebar"].pav-sb-closed {{
    transform: translateX(-{_SB_W + 10}px) !important;
}}
section[data-testid="stSidebar"] > div:first-child {{
    padding: 0 12px 16px !important;
    display: flex !important; flex-direction: column !important; min-height: 100vh !important;
}}

/* ── Esconde controles nativos ── */
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
button[aria-label="Close sidebar"],
button[aria-label="Open sidebar"],
[data-testid="stSidebarHeader"] {{ display: none !important; }}
section[data-testid="stSidebar"] .stButton {{ margin-bottom: 4px !important; }}

/* ── Conteúdo principal se ajusta à sidebar ── */
/* Sidebar ABERTA: empurra o main para a direita */
section[data-testid="stMain"] {{
    margin-left: {_SB_W}px !important;
    width: calc(100% - {_SB_W}px) !important;
    transition: margin-left 0.28s cubic-bezier(.4,0,.2,1),
                width      0.28s cubic-bezier(.4,0,.2,1) !important;
}}
/* Sidebar FECHADA: main ocupa tudo */
body.pav-sb-closed section[data-testid="stMain"] {{
    margin-left: 0 !important;
    width: 100% !important;
}}

/* ── Botão seta ── */
#pav-sb-btn {{
    position: fixed !important; top: 12px !important; left: {_SB_W + 8}px !important;
    z-index: 9999 !important; width: 26px !important; height: 26px !important;
    border-radius: 50% !important; background: #0f1824 !important;
    border: 1px solid #1a2535 !important; color: #e6edf3 !important;
    font-size: 11px !important; cursor: pointer !important;
    display: flex !important; align-items: center !important; justify-content: center !important;
    box-shadow: 0 2px 8px rgba(0,0,0,.6) !important;
    transition: left 0.28s cubic-bezier(.4,0,.2,1), background .15s !important;
    user-select: none !important;
}}
#pav-sb-btn:hover {{ background: #1a2535 !important; }}
#pav-sb-btn.pav-closed {{ left: 8px !important; }}

/* ── Páginas ── */
.pav-page {{ padding: 1.5rem 2rem; max-width: 820px; }}
div[data-testid="stButton"] > button {{
    border-radius: 12px !important; font-weight: 600 !important; transition: all .2s !important;
}}

/* ── Botão primário (Voice Mode ativo) → roxo ── */
section[data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"],
section[data-testid="stSidebar"] div[data-testid="stButton"] > button[data-testid="baseButton-primary"] {{
    background: linear-gradient(135deg, #6c3fc5, #8b5cf6) !important;
    border: 1px solid #7c4dcc !important;
    color: #fff !important;
    box-shadow: 0 0 12px rgba(139, 92, 246, 0.35) !important;
}}
section[data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"]:hover,
section[data-testid="stSidebar"] div[data-testid="stButton"] > button[data-testid="baseButton-primary"]:hover {{
    background: linear-gradient(135deg, #7c4dcc, #9d6ff7) !important;
    box-shadow: 0 0 18px rgba(139, 92, 246, 0.5) !important;
}}

::-webkit-scrollbar {{ width: 4px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: #1a2535; border-radius: 4px; }}

/* Esconde microfone nativo do Streamlit globalmente */
[data-testid="stAudioInput"],
[data-testid="stAudioInput"] *,
div:has(> [data-testid="stAudioInput"]) {{
    position: fixed !important;
    bottom: -9999px !important;
    left: -9999px !important;
    width: 1px !important;
    height: 1px !important;
    opacity: 0 !important;
    pointer-events: none !important;
    overflow: hidden !important;
}}
</style>""", unsafe_allow_html=True)


# =============================================================================
# SIDEBAR
# =============================================================================
def show_sidebar() -> None:
    user     = st.session_state.user
    username = user["username"]
    profile  = user.get("profile", {})
    lang     = profile.get("language", "pt-BR")
    page     = st.session_state.page

    components.html("""<!DOCTYPE html><html><head>
<style>html,body{margin:0;padding:0;overflow:hidden;background:transparent;}</style>
</head><body><script>
(function(){
    var KEY = 'pav_sb_open';
    var par = window.parent;
    var doc = par.document;
    function isOpen(){ try{ return par.sessionStorage.getItem(KEY) !== 'false'; }catch(e){ return true; } }
    function setOpen(v){ try{ par.sessionStorage.setItem(KEY, v ? 'true' : 'false'); }catch(e){} }
    function apply(){
        var sb  = doc.querySelector('section[data-testid="stSidebar"]');
        var btn = doc.getElementById('pav-sb-btn');
        if(!sb || !btn) return;
        var open = isOpen();
        // Sidebar: slide in/out
        sb.classList.toggle('pav-sb-closed', !open);
        // Body: controla margin do main content
        doc.body.classList.toggle('pav-sb-closed', !open);
        // Botão seta
        btn.classList.toggle('pav-closed', !open);
        btn.textContent = open ? '\u25c4' : '\u25ba';
    }
    function setup(){
        var btn = doc.getElementById('pav-sb-btn');
        if(!btn){ btn = doc.createElement('button'); btn.id = 'pav-sb-btn'; doc.body.appendChild(btn); }
        btn.onclick = function(e){ e.stopPropagation(); setOpen(!isOpen()); apply(); };
        apply();
    }
    setup();
    setTimeout(setup, 200); setTimeout(setup, 800); setTimeout(setup, 2000);
})();
</script></body></html>""", height=0)

    with st.sidebar:
        uav_html = user_avatar_html(username, size=62)
        st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;padding:24px 4px 16px;">
    {uav_html}
    <div>
        <div style="font-weight:700;font-size:1rem;color:#e6edf3;line-height:1.3;">{user.get('name','').split()[0]}</div>
        <div style="font-size:.72rem;color:#f0a500;margin-top:2px;">&#9679; Online</div>
    </div>
</div>
<hr style="border:none;border-top:1px solid #1a2535;margin:0 0 14px;"/>
""", unsafe_allow_html=True)

        nav_items = [
            ("voice",    f"🎙️ {t('voice_mode', lang)}"),
            ("settings", f"⚙️ {t('settings', lang)}"),
            ("history",  f"📄 {t('history', lang)}"),
        ]
        if user.get("role") == "professor":
            nav_items.append(("dashboard", f"📊 {t('dashboard', lang)}"))

        for pg, label in nav_items:
            active = page == pg
            if st.button(label, use_container_width=True, key=f"nav_{pg}",
                         type="primary" if active else "secondary"):
                st.session_state.page = pg
                st.rerun()

        if st.session_state.page == "voice":
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            if st.button(f"➕ {t('new_conv', lang)}", use_container_width=True, key="new_conv_btn"):
                st.session_state.conv_id = new_conversation(username)
                for k in ["_vm_history", "_vm_reply", "_vm_tts_b64", "_vm_user_said", "_vm_error", "_vm_last_upload"]:
                    st.session_state.pop(k, None)
                st.session_state["_vm_history"] = []
                st.rerun()

        st.markdown("<hr style='border:none;border-top:1px solid #1a2535;margin:10px 0;'/>",
                    unsafe_allow_html=True)

        st.markdown(f"""
<div style="padding:4px 4px 0;font-size:.72rem;color:#4a5a6a;line-height:2;">
    <b style="color:#8b949e;">{user.get('name','')}</b><br>
    {user.get('level','—')} &middot; {user.get('focus','—')}
</div>""", unsafe_allow_html=True)

        st.markdown("""<div style="flex:1;min-height:24px;"></div>
<hr style="border:none;border-top:1px solid #1a2535;margin:0 0 10px;"/>""",
                    unsafe_allow_html=True)

        if st.button(f"🚪 {t('logout', lang)}", use_container_width=True,
                     key="sb_logout", type="secondary"):
            _logout()
            st.rerun()