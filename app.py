import os, json, base64
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import streamlit.components.v1 as components
import anthropic
from datetime import datetime

from database import (
    init_db, authenticate, register_student, load_students,
    new_conversation, list_conversations, load_conversation,
    append_message, get_all_students_stats, delete_conversation,
    update_profile, update_password,
    create_session, validate_session, delete_session,
    save_user_avatar_db, get_user_avatar_db, remove_user_avatar_db,
)
from transcriber import transcribe_bytes
from tts import text_to_speech, tts_available

# Font Awesome
st.markdown(
    '<link rel="stylesheet" '
    'href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">',
    unsafe_allow_html=True,
)

# =============================================================================
# INIT DB
# =============================================================================
init_db()

# =============================================================================
# ENV
# =============================================================================
API_KEY   = os.getenv("ANTHROPIC_API_KEY", "")
PROF_NAME = os.getenv("PROFESSOR_NAME", "Teacher Tati")
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
        "new_conv":           "Nova conversa",
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
        # Configurações
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
        # Aparência
        "section_appearance": "🎨 Aparência",
        "ring_color":         "Cor do anel da professora",
        "user_bubble_color":  "Cor da sua bolha",
        "bot_bubble_color":   "Cor da bolha da IA",
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
        "new_conv":           "New conversation",
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
        # Settings
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
        # Appearance
        "section_appearance": "🎨 Appearance",
        "ring_color":         "Professor ring colour",
        "user_bubble_color":  "Your bubble colour",
        "bot_bubble_color":   "AI bubble colour",
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
        "new_conv":           "New conversation",
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
        # Settings
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
        # Appearance
        "section_appearance": "🎨 Appearance",
        "ring_color":         "Professor ring colour",
        "user_bubble_color":  "Your bubble colour",
        "bot_bubble_color":   "AI bubble colour",
        "appearance_hint":    "Colours apply instantly in conversation mode.",
    },
}

def t(key: str, lang: str = "pt-BR") -> str:
    return _STRINGS.get(lang, _STRINGS["pt-BR"]).get(key, key)

# =============================================================================
# SYSTEM PROMPT
# =============================================================================
SYSTEM_PROMPT = f"""You are a digital avatar of an English teacher called {PROF_NAME} -- warm, witty, very intelligent and encouraging. You help adults speak English with more confidence, over 25 years of experience, Advanced English Hunter College NY, and passionate about teaching.

BILINGUAL POLICY (VERY IMPORTANT)
The student's messages may arrive in English, Portuguese, or a mix.

BEGINNER / PRE-INTERMEDIATE:
  * Student writes/speaks in Portuguese -> Fully acceptable. Respond in simple English
    AND provide the Portuguese translation of key words in parentheses.
  * Always end your reply with an easy, encouraging question in English.

INTERMEDIATE:
  * Respond primarily in English. Use Portuguese ONLY to clarify a specific word.
  * If the student writes in Portuguese, invite them to try in English.

ADVANCED / BUSINESS ENGLISH:
  * Respond exclusively in English.
  * "Let's keep it in English -- you've got this!"

TEACHING STYLE:
- Neuro-learning: guide students to discover errors.
- Sandwich: 1) Validate 2) Guide with question 3) Encourage.
- SHORT conversational responses for voice. Max 3 sentences.
- End with ONE engaging question.
- NO markdown, NO bullet points -- plain natural speech for TTS.
- NEVER start uninvited. Wait for the student to speak first."""

# =============================================================================
# SESSION STATE
# =============================================================================
_DEFAULTS = {
    "logged_in":   False,
    "user":        None,
    "page":        "voice",       # voice | settings | history | dashboard
    "conv_id":     None,
    "audio_key":   0,
    "_vm_history": [],
    "_vm_reply":   "",
    "_vm_tts_b64": "",
    "_vm_user_said": "",
    "_vm_error":   "",
    "_vm_last_upload": None,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =============================================================================
# HELPERS
# =============================================================================
#@st.cache_data(show_spinner=False)
def get_photo_b64() -> str | None:
    """Lê a foto da professora e devolve como data-URI base64."""
    p = Path(PHOTO_PATH)
    if p.exists():
        ext  = p.suffix.lower().replace(".", "")
        mime = "jpeg" if ext in ("jpg", "jpeg") else ext
        return f"data:image/{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"
    return None

PHOTO_B64 = get_photo_b64()

#@st.cache_data(show_spinner=False)
def get_tati_mini_b64() -> str:
    """Lê a foto da Tati uma única vez e reutiliza em todo o app."""
    for _p in [Path("assets/tati.png"), Path("assets/tati.jpg"),
               Path(__file__).parent / "assets" / "tati.png",
               Path(__file__).parent / "assets" / "tati.jpg"]:
        if _p.exists():
            _ext  = _p.suffix.lstrip(".").lower()
            _mime = "jpeg" if _ext in ("jpg", "jpeg") else _ext
            return f"data:image/{_mime};base64,{base64.b64encode(_p.read_bytes()).decode()}"
    return get_photo_b64() or ""

# ── Cache dos 4 frames do avatar animado do modo voz ─────────────────────────
#@st.cache_data(show_spinner=False)
def get_avatar_frames() -> dict:
    """Carrega os frames do avatar animado uma única vez."""
    _base = Path(__file__).parent
    def _load(candidates):
        for p in candidates:
            p = Path(p)
            if p.exists():
                return f"data:image/png;base64,{base64.b64encode(p.read_bytes()).decode()}"
        return ""
    return {
        "base":   _load([_base/"assets"/"avatar_tati_normal.png",      "assets/avatar_tati_normal.png"]),
        "closed": _load([_base/"assets"/"avatar_tati_closed.png",      "assets/avatar_tati_closed.png"]),
        "mid":    _load([_base/"assets"/"avatar_tati_meio.png",        "assets/avatar_tati_meio.png"]),
        "open":   _load([_base/"assets"/"avatar_tati_bem_aberta.png",  "assets/avatar_tati_bem_aberta.png",
                         _base/"assets"/"avatar_tati_aberta.png",      "assets/avatar_tati_aberta.png"]),
    }

# ── Avatares individuais dos alunos ───────────────────────────────────────────
def _get_avatar(username: str) -> str | None:
    """Busca foto do usuário direto do banco, sem cache."""
    result = get_user_avatar_db(username)
    if not result:
        return None
    raw, mime = result
    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"

# Mantém get_user_avatar_b64 como alias para compatibilidade (sidebar etc.)
def get_user_avatar_b64(username: str) -> str | None:
    return _get_avatar(username)

def save_user_avatar(username: str, raw: bytes, suffix: str) -> None:
    """Salva a foto de perfil no Supabase Storage."""
    suffix = suffix.lower().lstrip(".")
    mime   = "image/jpeg" if suffix in ("jpg", "jpeg") else f"image/{suffix}"
    save_user_avatar_db(username, raw, mime)

def remove_user_avatar(username: str) -> None:
    """Remove a foto de perfil do Supabase Storage."""
    remove_user_avatar_db(username)

def _avatar_circle_html(b64: str | None, size: int, border: str = "#f0a500") -> str:
    """Retorna HTML de avatar circular — foto do usuário ou sem_foto.png."""
    if not b64:
        # Tenta carregar sem_foto.png como fallback
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
    # Fallback final: ícone FA
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
    """Retorna HTML de avatar circular do usuário."""
    return _avatar_circle_html(_get_avatar(username), size)

def avatar_html(size: int = 52, speaking: bool = False) -> str:
    """Avatar da professora — background-image evita flash do <img>."""
    cls   = "speaking" if speaking else ""
    photo = PHOTO_B64
    if photo:
        return (
            f'<div class="avatar-wrap {cls}" style="'
            f'width:{size}px;height:{size}px;border-radius:50%;flex-shrink:0;'
            f'background:url({photo}) center top/cover no-repeat;'
            f'position:relative;overflow:hidden;">'
            f'<div class="avatar-ring"></div></div>'
        )
    return (
        f'<div class="avatar-circle {cls}" '
        f'style="width:{size}px;height:{size}px;font-size:{int(size*.48)}px">🧑‍🏫</div>'
    )

#for p in [Path(PHOTO_PATH), Path("assets/tati.png"), Path("assets/tati.jpg"),
 #             Path("assets/professor.jpg"), Path("assets/professor.png")]:
  #      if p.exists():
   #         ext = p.suffix.lstrip(".").lower()
    #        mime = "jpeg" if ext in ("jpg","jpeg") else ext
     #       return f"data:image/{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"
    #return ""

#@st.cache_data(show_spinner=False)
#def get_avatar_frames() -> dict:
 #   base_ = Path("assets")
 #   def _load(candidates):
 #       for c in candidates:
#            p = base_ / c
#            if p.exists():
#                ext = p.suffix.lstrip(".").lower()
#                mime = "jpeg" if ext in ("jpg","jpeg") else ext
#                return f"data:image/{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"
 #       return ""
 #   return {
  #      "base":   _load(["tati.png","tati.jpg","avatar_base.png","professor.jpg"]),
 #       "closed": _load(["avatar_closed.png","tati_closed.png"]),
 #       "mid":    _load(["avatar_mid.png","tati_mid.png"]),
 #       "open":   _load(["avatar_open.png","tati_open.png"]),
 #   }

def get_or_create_conv(username: str) -> str:
    if st.session_state.conv_id:
        return st.session_state.conv_id
    convs = list_conversations(username)
    if convs:
        cid = convs[0]["id"]
    else:
        cid = new_conversation(username)
    st.session_state.conv_id = cid
    return cid

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
    for k, v in _DEFAULTS.items():
        st.session_state[k] = v
    # garante que próximo login salva o token novamente
    st.session_state.pop("_session_saved", None)

def js_save_session(token: str) -> None:
    """Salva token no localStorage E no cookie (max-age 30 dias)."""
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
    try{{
        var exp2=new Date(Date.now()+2592000000).toUTCString();
        document.cookie='pav_session='+encodeURIComponent(t)+';expires='+exp2+';path=/;SameSite=Lax';
    }}catch(e){{}}
}})();
</script></body></html>""", height=1)

# =============================================================================
# GLOBAL CSS
# =============================================================================
st.markdown("""<style>
/* ---- Reset Streamlit ---- */
#MainMenu, footer, header { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
section[data-testid="stMain"] > div {
    max-width: 100% !important;
    padding: 0 !important;
}
.main .block-container {
    max-width: 100% !important;
    padding: 0 !important;
}
/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {
    background: #070c15 !important;
    border-right: 1px solid #1a2535 !important;
    min-width: 240px !important;
    max-width: 300px !important;
}
/* ---- Botoes Streamlit base ---- */
div[data-testid="stButton"] > button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    transition: all .2s !important;
}
/* ---- Scrollbar ---- */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #1a2535; border-radius: 4px; }
</style>""", unsafe_allow_html=True)

# =============================================================================
# TELA DE LOGIN
# =============================================================================
def show_login() -> None:
    photo_src = get_photo_b64()

    # Auto-login JS (localStorage/cookie -> query param)
    components.html("""<!DOCTYPE html><html><head>
<style>html,body{margin:0;padding:0;overflow:hidden;}</style>
</head><body><script>
(function(){
    function readToken(){
        // 1) localStorage do parent (mais confiável)
        try{var s=window.parent.localStorage.getItem('pav_session');if(s&&s.length>10)return s;}catch(e){}
        // 2) localStorage do próprio iframe
        try{var s2=localStorage.getItem('pav_session');if(s2&&s2.length>10)return s2;}catch(e){}
        // 3) Cookie do parent
        try{var m=window.parent.document.cookie.split(';').map(function(c){return c.trim();})
            .find(function(c){return c.startsWith('pav_session=');});
            if(m){var v=decodeURIComponent(m.split('=')[1]);if(v&&v.length>10)return v;}}catch(e){}
        // 4) Cookie do iframe
        try{var m2=document.cookie.split(';').map(function(c){return c.trim();})
            .find(function(c){return c.startsWith('pav_session=');});
            if(m2){var v2=decodeURIComponent(m2.split('=')[1]);if(v2&&v2.length>10)return v2;}}catch(e){}
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

    # Sem sidebar na tela de login
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
           font-size:38px;margin:0 auto 14px;
           box-shadow:0 0 0 6px rgba(240,165,0,.1);}}
h2{{font-size:1.4rem;font-weight:800;text-align:center;margin:0 0 4px;
    background:linear-gradient(135deg,#f0a500 30%,#e05c2a 100%);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
p{{font-size:.72rem;color:#3a4e5e;text-align:center;}}
</style></head><body>
<div class="wrap"><div class="card">
    {('<div class="av" style="background:url('+photo_src+') center top/cover no-repeat;width:84px;height:84px;border-radius:50%;display:block;margin:0 auto 14px;border:2.5px solid #f0a500;box-shadow:0 0 0 6px rgba(240,165,0,.1),0 0 32px rgba(240,165,0,.2);"></div>') if photo_src else "<div class=\'av-emoji\'>&#129489;&#8205;&#127979;</div>"}
    <h2>{PROF_NAME}</h2>
    <p>Voice English Coach</p>
</div></div>
</body></html>""", height=260, scrolling=False)

        # Tabs
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
        if login_err: st.error(f"&#10060; {login_err}")
        if reg_err:   st.error(f"&#10060; {reg_err}")
        if reg_ok:    st.success(f"&#9989; Conta criada! Bem-vindo(a), {reg_name}!")

        if st.session_state["_login_tab"] == "login":
            with st.form("form_login", clear_on_submit=True):
                u = st.text_input(t("username"), placeholder="seu.usuario")
                p = st.text_input(t("password"), type="password", placeholder="••••••••")
                submitted = st.form_submit_button(t("enter"), use_container_width=True)
                if submitted:
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
                rn = st.text_input(t("full_name"),  placeholder="João Silva")
                re_ = st.text_input(t("email"),     placeholder="joao@email.com")
                ru = st.text_input(t("username"),   placeholder="joao.silva")
                rp = st.text_input("Senha", type="password", placeholder="minimo 6 caracteres")
                submitted = st.form_submit_button(t("create_account"), use_container_width=True)
                if submitted:
                    if not rn or not re_ or not ru or not rp:
                        st.session_state["_reg_err"] = "Preencha todos os campos."
                        st.rerun()
                    elif "@" not in re_:
                        st.session_state["_reg_err"] = "E-mail invalido."
                        st.rerun()
                    elif len(rp) < 6:
                        st.session_state["_reg_err"] = "Senha muito curta (minimo 6)."
                        st.rerun()
                    else:
                        ok, msg = register_student(ru, rn, rp, email=re_)
                        if ok:
                            st.session_state["_reg_ok"]   = True
                            st.session_state["_reg_name"]  = rn
                            st.session_state["_login_tab"] = "login"
                            st.rerun()
                        else:
                            st.session_state["_reg_err"] = msg
                            st.rerun()

        st.markdown(
            f'<p style="text-align:center;font-size:.6rem;color:#1a2535;margin-top:14px;">'
            f'2025 &copy; {PROF_NAME}</p>',
            unsafe_allow_html=True,
        )

# =============================================================================
# SIDEBAR (quando logado)
# =============================================================================
def show_sidebar() -> None:
    user     = st.session_state.user
    username = user["username"]
    profile  = user.get("profile", {})
    lang     = profile.get("language", "pt-BR")
    page     = st.session_state.page

    with st.sidebar:
        # Avatar do aluno + nome
        uav_html = user_avatar_html(username, size=52, fallback_emoji="🎓")

        st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;padding:16px 8px 12px;">
    {uav_html}
    <div>
        <div style="font-weight:700;font-size:.95rem;color:#e6edf3;">{user.get('name','').split()[0]}</div>
        <div style="font-size:.7rem;color:#f0a500;">&#9679; Online</div>
    </div>
</div>
<hr style="border:none;border-top:1px solid #1a2535;margin:0 0 10px;"/>
""", unsafe_allow_html=True)

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        # Navegação
        nav_items = [
            ("voice",    "&#127908; " + t("voice_mode", lang) if "voice_mode" in _STRINGS["pt-BR"]
                         else "&#127908; Modo Conversa"),
            ("settings", "&#9881; "  + t("settings", lang)),
            ("history",  "&#128196; " + t("history", lang)),
        ]
        if user.get("role") == "professor":
            nav_items.append(("dashboard", "&#128202; " + t("dashboard", lang)))

        for pg, label in nav_items:
            active = page == pg
            btn_type = "primary" if active else "secondary"
            if st.button(label, use_container_width=True, key=f"nav_{pg}", type=btn_type):
                st.session_state.page = pg
                st.rerun()

            # Botão nova conversa de voz
        if st.session_state.page == "voice":
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            if st.button("➕ Nova conversa", use_container_width=True, key="new_conv_btn"):
                st.session_state.conv_id = new_conversation(username)
                for k in ["_vm_history", "_vm_reply", "_vm_tts_b64",
                          "_vm_user_said", "_vm_error", "_vm_last_upload"]:
                    st.session_state.pop(k, None)
                st.session_state["_vm_history"] = []
                st.rerun()

        st.markdown("<hr style='border:none;border-top:1px solid #1a2535;margin:10px 0;'/>",
                    unsafe_allow_html=True)

        # Info do aluno
        st.markdown(f"""
<div style="padding:0 4px;font-size:.72rem;color:#4a5a6a;line-height:1.8;">
    <b style="color:#8b949e;">{user.get('name','')}</b><br>
    {user.get('level','—')} &middot; {user.get('focus','—')}
</div>
""", unsafe_allow_html=True)

        st.markdown("<div style='flex:1'></div>", unsafe_allow_html=True)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # Sair
        if st.button("&#128682; " + t("logout", lang), use_container_width=True, key="sb_logout",
                     type="secondary"):
            _logout(); st.rerun()

# =============================================================================
# PROCESSAR AUDIO → CLAUDE → TTS
# =============================================================================
def process_voice(raw: bytes, conv_id: str) -> None:
    user     = st.session_state.user
    username = user["username"]
    profile  = user.get("profile", {})
    lang     = profile.get("language", "pt-BR")

    txt = transcribe_bytes(raw, suffix=".webm", language=None)
    if not txt or txt.startswith("&#10060;") or txt.startswith("&#9888;"):
        st.session_state["_vm_error"] = txt or t("error_mic", lang)
        return

    st.session_state["_vm_user_said"] = txt
    if not API_KEY:
        st.session_state["_vm_error"] = t("error_api", lang)
        return

    history = st.session_state.get("_vm_history", [])
    context = (
        f"\n\nStudent profile -- Name: {user.get('name','')} | "
        f"Level: {user.get('level','Beginner')} | "
        f"Focus: {user.get('focus','General Conversation')} | "
        f"Native language: Brazilian Portuguese."
    )

    history.append({"role": "user", "content": txt})
    client = anthropic.Anthropic(api_key=API_KEY)
    resp   = client.messages.create(
        model="claude-haiku-4-5", max_tokens=400,
        system=SYSTEM_PROMPT + context, messages=history,
    )
    reply = resp.content[0].text
    history.append({"role": "assistant", "content": reply})
    st.session_state["_vm_history"] = history

    tts_b64 = ""
    if tts_available():
        ab = text_to_speech(reply)
        if ab:
            tts_b64 = base64.b64encode(ab).decode()

    st.session_state["_vm_reply"]   = reply
    st.session_state["_vm_tts_b64"] = tts_b64

    append_message(username, conv_id, "user",      txt,   audio=True)
    append_message(username, conv_id, "assistant", reply, tts_b64=tts_b64 or None)

# =============================================================================
# TELA PRINCIPAL — MODO VOZ
# =============================================================================
def show_voice() -> None:
    user     = st.session_state.user
    username = user["username"]
    profile  = user.get("profile", {})
    lang     = profile.get("language", "pt-BR")
    speech_lang = profile.get("speech_lang", "en-US")

    # Cores personalizadas do usuário
    ring_color       = profile.get("ring_color",        "#f0a500")
    user_bubble_color = profile.get("user_bubble_color", "#2d6a4f")
    bot_bubble_color  = profile.get("bot_bubble_color",  "#1a1f2e")

    def _rgba(hex_color: str, alpha: float) -> str:
        h = hex_color.lstrip("#")
        if len(h) == 3: h = h[0]*2 + h[1]*2 + h[2]*2
        r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return f"rgba({r},{g},{b},{alpha})"

    conv_id = get_or_create_conv(username)

    # Carrega histórico do banco se _vm_history estiver vazio (ex: ao abrir conversa do histórico)
    if not st.session_state.get("_vm_history") and conv_id:
        msgs_db = load_conversation(username, conv_id)
        if msgs_db:
            st.session_state["_vm_history"] = [
                {"role": m["role"], "content": m["content"]}
                for m in msgs_db
                if m.get("content")
            ]

    # Processa áudio recebido
    audio_val = st.audio_input(
        " ", key=f"voice_input_{st.session_state.audio_key}",
        label_visibility="collapsed",
    )
    if audio_val and audio_val != st.session_state.get("_vm_last_upload"):
        st.session_state["_vm_last_upload"] = audio_val
        for k in ["_vm_reply","_vm_tts_b64","_vm_user_said","_vm_error"]:
            st.session_state.pop(k, None)
        with st.spinner(t("processing", lang)):
            process_voice(audio_val.read(), conv_id)
        st.session_state.audio_key += 1
        st.rerun()

    # Dados do estado
    user_said = st.session_state.get("_vm_user_said", "")
    reply     = st.session_state.get("_vm_reply",     "")
    tts_b64   = st.session_state.get("_vm_tts_b64",   "")
    vm_error  = st.session_state.get("_vm_error",     "")

    # Frames do avatar
    frames  = get_avatar_frames()
    av_base   = frames["base"]
    av_closed = frames["closed"]
    av_mid    = frames["mid"]
    av_open   = frames["open"]
    has_anim  = bool(av_base and av_closed and av_mid and av_open)

    is_speaking = bool(reply and tts_b64)

    # Passa o histórico completo para o JS renderizar todas as bolhas
    history    = st.session_state.get("_vm_history", [])
    history_js = json.dumps(history)

    tts_js    = json.dumps(tts_b64)
    reply_js  = json.dumps(reply)
    us_js     = json.dumps(user_said)
    err_js    = json.dumps(vm_error)
    sl_js     = json.dumps(speech_lang)
    tap_speak = json.dumps(t("tap_to_speak", lang))
    tap_stop  = json.dumps(t("tap_to_stop",  lang))
    speaking_ = json.dumps(t("speaking_ai",  lang))
    proc_     = json.dumps(t("processing",   lang))

    av_b64_js  = json.dumps(av_base)
    avc_js     = json.dumps(av_closed)
    avm_js     = json.dumps(av_mid)
    avo_js     = json.dumps(av_open)
    has_anim_js = "true" if has_anim else "false"
    # Usa tati como fallback estático (não professor.jpg)
    photo_js   = json.dumps(get_tati_mini_b64() or get_photo_b64())

    components.html(f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
html,body{{
    background:#060a10;font-family:'Sora',sans-serif;
    height:100%;overflow:hidden;
}}
.app{{
    display:flex;flex-direction:column;align-items:center;
    height:100vh;padding:16px 20px 0;
    gap:10px;overflow:hidden;
}}
/* ---- Avatar ---- */
.avatar-wrap{{
    position:relative;width:120px;height:120px;flex-shrink:0;
    margin-top:4px;
}}
.avatar-ring{{
    position:absolute;inset:-8px;border-radius:50%;
    border:2px solid {_rgba(ring_color,.3)};
    animation:ring-pulse 2s ease-in-out infinite;
}}
.avatar-ring.active{{
    border-color:{ring_color};
    box-shadow:0 0 0 0 {_rgba(ring_color,.5)};
    animation:ring-glow 1s ease-in-out infinite;
}}
@keyframes ring-pulse{{0%,100%{{opacity:.4;transform:scale(1);}}50%{{opacity:.8;transform:scale(1.03);}}}}
@keyframes ring-glow{{0%{{box-shadow:0 0 0 0 {_rgba(ring_color,.5)};}}70%{{box-shadow:0 0 14px {_rgba(ring_color,0)};}}100%{{box-shadow:0 0 0 0 {_rgba(ring_color,0)};}}}}
.avatar-img{{
    width:120px;height:120px;border-radius:50%;
    object-fit:cover;object-position:top;
    border:3px solid {ring_color};
    box-shadow:0 0 32px {_rgba(ring_color,.25)};
}}
.avatar-emoji{{
    width:120px;height:120px;border-radius:50%;
    background:linear-gradient(135deg,#1a2535,#0f1824);
    border:3px solid {ring_color};
    display:flex;align-items:center;justify-content:center;
    font-size:54px;
    box-shadow:0 0 32px rgba(240,165,0,.2);
}}
.prof-name{{font-size:1rem;font-weight:700;color:#e6edf3;margin-top:6px;}}
.status{{font-size:.68rem;color:{ring_color};margin-top:1px;}}

/* ---- Historico de bolhas ---- */
.history-wrap{{
    width:100%;max-width:1100px;
    flex:1;min-height:0;
    overflow-y:auto;display:flex;flex-direction:column;gap:8px;
    padding:8px 4px;
    scrollbar-width:thin;scrollbar-color:#1a2535 transparent;
}}
.history-wrap::-webkit-scrollbar{{width:4px;}}
.history-wrap::-webkit-scrollbar-thumb{{background:#1a2535;border-radius:4px;}}
.history-wrap::-webkit-scrollbar-track{{background:transparent;}}
.bubble{{
    max-width:82%;padding:10px 15px;border-radius:18px;
    font-size:.84rem;line-height:1.55;word-break:normal;
}}
.bubble.user{{
    align-self:flex-end;
    background:{user_bubble_color};color:#d8f3dc;
    border-bottom-right-radius:4px;
}}
.bubble.bot{{
    align-self:flex-start;
    background:{bot_bubble_color};color:#e6edf3;
    border:1px solid {_rgba(bot_bubble_color,.6)};
    border-bottom-left-radius:4px;
}}
.bubble-label{{font-size:.6rem;color:#4a5a6a;margin:2px 4px;}}
.bubble-label.right{{text-align:right;}}

/* ---- Transcricao atual — removida, integrada nas bolhas ---- */
.transcript-box{{display:none;}}

/* ---- Mic fixo no rodapé ---- */
.mic-footer{{
    flex-shrink:0;
    width:100%;max-width:560px;
    display:flex;flex-direction:column;align-items:center;
    gap:8px;
    padding:12px 0 20px;
    background:linear-gradient(to top,#060a10 70%,transparent);
    position:sticky;bottom:0;
}}
.mic-btn{{
    width:72px;height:72px;border-radius:50%;border:none;cursor:pointer;
    background:linear-gradient(135deg,#1a2535,#131c2a);
    color:#8b949e;font-size:28px;
    display:flex;align-items:center;justify-content:center;
    box-shadow:0 4px 20px rgba(0,0,0,.4),inset 0 1px 0 rgba(255,255,255,.05);
    transition:all .2s;outline:none;
    position:relative;
}}
.mic-btn:hover{{background:linear-gradient(135deg,#1e2f40,#182130);color:#e6edf3;}}
.mic-btn.recording{{
    background:linear-gradient(135deg,#e05c2a,#c44a1a);
    color:#fff;
    box-shadow:0 0 0 0 rgba(224,92,42,.6),0 4px 20px rgba(224,92,42,.3);
    animation:mic-pulse 1.2s ease-in-out infinite;
}}
.mic-btn.processing{{
    background:linear-gradient(135deg,#f0a500,#c88800);
    color:#060a10;
    animation:none;
}}
@keyframes mic-pulse{{
    0%{{box-shadow:0 0 0 0 rgba(224,92,42,.6),0 4px 20px rgba(224,92,42,.3);}}
    70%{{box-shadow:0 0 0 16px rgba(224,92,42,0),0 4px 20px rgba(224,92,42,.3);}}
    100%{{box-shadow:0 0 0 0 rgba(224,92,42,0),0 4px 20px rgba(224,92,42,.3);}}
}}
.mic-hint{{font-size:.68rem;color:#4a5a6a;letter-spacing:.3px;}}

/* ---- Error ---- */
.error-box{{
    background:rgba(224,92,42,.1);border:1px solid rgba(224,92,42,.3);
    border-radius:10px;padding:8px 14px;font-size:.78rem;color:#e05c2a;
    max-width:560px;width:100%;text-align:center;
    flex-shrink:0;
}}
</style>
</head><body>
<div class="app" id="app">

    <!-- Avatar -->
    <div style="display:flex;flex-direction:column;align-items:center;gap:4px;">
        <div class="avatar-wrap">
            <div class="avatar-ring" id="ring"></div>
            <img id="avImg" class="avatar-img"
                 src="" alt="{PROF_NAME}"
                 onerror="this.style.display='none';document.getElementById('avEmoji').style.display='flex';"
                 style="display:none;width:120px;height:120px;">
            <div id="avEmoji" class="avatar-emoji">&#129489;&#8205;&#127979;</div>
        </div>
        <div class="prof-name">{PROF_NAME}</div>
        <div class="status" id="statusTxt">&#9679; Online</div>
    </div>

    <!-- Historico de bolhas -->
    <div class="history-wrap" id="historyWrap"></div>

    <!-- Erro -->
    <div class="error-box" id="errBox" style="display:none;"></div>

    <!-- Transcricao (oculta — mantida por compatibilidade JS) -->
    <div class="transcript-box" id="transcriptBox" style="display:none;"></div>

    <!-- Mic fixo no rodape -->
    <div class="mic-footer">
        <button class="mic-btn" id="micBtn" title="Gravar">
            <i class="fa-solid fa-microphone"></i>
        </button>
        <div class="mic-hint" id="micHint">{t("tap_to_speak", lang)}</div>
    </div>

</div>

<!-- Font Awesome local -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">

<script>
(function(){{

// ---- Dados do estado Python ----
var TTS_B64    = {tts_js};
var REPLY      = {reply_js};
var USER_SAID  = {us_js};
var HISTORY    = {history_js};
var VM_ERROR   = {err_js};
var SPEECH_LANG= {sl_js};
var TAP_SPEAK  = {tap_speak};
var TAP_STOP   = {tap_stop};
var SPEAKING   = {speaking_};
var PROC       = {proc_};
var HAS_ANIM   = {has_anim_js};
var AV_BASE    = {av_b64_js};
var AV_CLOSED  = {avc_js};
var AV_MID     = {avm_js};
var AV_OPEN    = {avo_js};
var PHOTO      = {photo_js};

// ---- Elementos ----
var micBtn   = document.getElementById('micBtn');
var micHint  = document.getElementById('micHint');
var statusTxt= document.getElementById('statusTxt');
var transBox = document.getElementById('transcriptBox');
var errBox   = document.getElementById('errBox');
var ring     = document.getElementById('ring');
var avImg    = document.getElementById('avImg');
var avEmoji  = document.getElementById('avEmoji');
var histWrap = document.getElementById('historyWrap');

// ---- Avatar ----
var photoSrc = HAS_ANIM ? AV_BASE : (PHOTO || AV_BASE);
if(photoSrc){{
    avImg.src = photoSrc;
    avImg.style.display = 'block';
    avEmoji.style.display = 'none';
}}

// ---- Anima boca ----
var mouthFrames = HAS_ANIM ? [AV_BASE, AV_CLOSED, AV_MID, AV_OPEN] : null;
var mouthTimer  = null;
var mouthIdx    = 0;
var analyser     = null;
var audioCtx     = null;

function stopMouthAnim(){{
    if(mouthTimer){{ clearInterval(mouthTimer); mouthTimer=null; }}
    if(HAS_ANIM && avImg.src !== AV_BASE){{ avImg.src = AV_BASE; }}
}}

function startMouthAnim(audioEl){{
    if(!HAS_ANIM)return;
    try{{
        if(!audioCtx){{ audioCtx=new(window.AudioContext||window.webkitAudioContext)(); }}
        if(!analyser){{
            analyser=audioCtx.createAnalyser();
            analyser.fftSize=256;
            var src=audioCtx.createMediaElementSource(audioEl);
            src.connect(analyser);
            analyser.connect(audioCtx.destination);
        }}
        var buf=new Uint8Array(analyser.frequencyBinCount);
        mouthTimer=setInterval(function(){{
            analyser.getByteFrequencyData(buf);
            var vol=buf.reduce(function(a,b){{return a+b;}},0)/buf.length/128;
            if(vol<0.05)      avImg.src=AV_BASE;
            else if(vol<0.2)  avImg.src=AV_CLOSED;
            else if(vol<0.5)  avImg.src=AV_MID;
            else              avImg.src=AV_OPEN;
        }},80);
    }}catch(e){{ mouthTimer=setInterval(function(){{
        mouthIdx=(mouthIdx+1)%4;
        var f=[AV_BASE,AV_CLOSED,AV_MID,AV_OPEN];
        avImg.src=f[mouthIdx];
    }},200); }}
}}

// ---- Audio TTS ----
var currentAudio = null;
function playTTS(b64){{
    if(currentAudio){{ currentAudio.pause(); currentAudio=null; stopMouthAnim(); }}
    if(!b64)return;
    ring.classList.add('active');
    statusTxt.textContent = SPEAKING;
    var audio = new Audio('data:audio/mp3;base64,'+b64);
    currentAudio = audio;
    audio.onplay    = function(){{ startMouthAnim(audio); }};
    audio.onended   = function(){{ stopMouthAnim(); ring.classList.remove('active'); statusTxt.textContent='&#9679; Online'; currentAudio=null; }};
    audio.onerror   = function(){{ stopMouthAnim(); ring.classList.remove('active'); statusTxt.textContent='&#9679; Online'; }};

    // Fallback SpeechSynthesis se TTS falhar
    if(!b64 && REPLY){{
        var utt=new SpeechSynthesisUtterance(REPLY);
        utt.lang=SPEECH_LANG;
        window.speechSynthesis.speak(utt);
        return;
    }}
    audio.play().catch(function(){{
        if(REPLY){{
            var utt=new SpeechSynthesisUtterance(REPLY);
            utt.lang=SPEECH_LANG;
            window.speechSynthesis.speak(utt);
        }}
    }});
}}

// ---- Historico de bolhas ----
function addBubble(role, text){{
    var label = document.createElement('div');
    label.className='bubble-label'+(role==='user'?' right':'');
    label.textContent = role==='user' ? 'Voce' : '{PROF_NAME}';
    var bub = document.createElement('div');
    bub.className='bubble '+role;
    bub.textContent = text;
    histWrap.appendChild(label);
    histWrap.appendChild(bub);
    histWrap.scrollTop=histWrap.scrollHeight;
}}

// ---- Mostrar estado atual ----
if(VM_ERROR){{
    errBox.textContent = VM_ERROR;
    errBox.style.display='block';
    transBox.textContent = TAP_SPEAK;
    transBox.classList.remove('active');
}} else {{
    errBox.style.display='none';
    // Renderiza todo o histórico acumulado
    if(HISTORY && HISTORY.length > 0){{
        HISTORY.forEach(function(msg){{
            addBubble(msg.role === 'user' ? 'user' : 'bot', msg.content);
        }});
    }}
    if(TTS_B64){{
        setTimeout(function(){{ playTTS(TTS_B64); }}, 400);
    }}
}}

// ---- Mic: ativa gravar no Streamlit ----
var par = window.parent;
var recording = false;

function getRealMicBtn(){{
    var doc = par ? par.document : document;
    var ai  = doc.querySelector('[data-testid="stAudioInput"]');
    if(!ai)return null;
    return ai.querySelector('button') || ai.querySelector('[data-testid="stAudioInputRecordButton"]');
}}

micBtn.onclick = function(){{
    var realBtn = getRealMicBtn();
    if(!realBtn)return;
    if(recording){{
        // parar
        micBtn.classList.remove('recording');
        micBtn.innerHTML='<i class="fa-solid fa-microphone"></i>';
        micHint.textContent = PROC;
        micBtn.classList.add('processing');
        recording=false;
        realBtn.click();
    }} else {{
        // iniciar
        if(currentAudio){{ currentAudio.pause(); currentAudio=null; stopMouthAnim(); ring.classList.remove('active'); }}
        if(par && par.speechSynthesis) par.speechSynthesis.cancel();
        micBtn.classList.add('recording');
        micBtn.innerHTML='<i class="fa-solid fa-stop"></i>';
        micHint.textContent = TAP_STOP;
        recording=true;
        realBtn.click();
    }}
}};

// ---- Esconde o stAudioInput nativo ----
function hideNativeAudio(){{
    var doc = par ? par.document : document;
    var ai  = doc.querySelector('[data-testid="stAudioInput"]');
    if(ai){{
        ai.style.position='fixed';
        ai.style.bottom='-999px';
        ai.style.left='-9999px';
        ai.style.opacity='0';
        ai.style.pointerEvents='none';
        ai.style.width='1px';
        ai.style.height='1px';
        // mas o botao interno deve ser clicavel
        var btn=ai.querySelector('button');
        if(btn)btn.style.pointerEvents='auto';
    }}
}}
hideNativeAudio();
try{{
    var doc2=par?par.document:document;
    var obs=new MutationObserver(hideNativeAudio);
    obs.observe(doc2.body,{{childList:true,subtree:true}});
    setTimeout(function(){{obs.disconnect();}},15000);
}}catch(e){{}}

}})();
</script>
</body></html>""", height=950, scrolling=False)

# =============================================================================
# TELA DE CONFIGURACOES
# =============================================================================
def show_settings() -> None:
    user     = st.session_state.user
    username = user["username"]
    profile  = user.get("profile", {})
    lang     = profile.get("language", "pt-BR")

    st.markdown("""<style>
.main .block-container{padding-top:1.5rem!important;}
</style>""", unsafe_allow_html=True)

    st.markdown(f"<h2 style='color:#e6edf3;margin-bottom:1rem;'>&#9881; {t('settings',lang)}</h2>",
                unsafe_allow_html=True)

    # ---- Foto de Perfil ----
    st.markdown(f"### {t('section_photo', lang)}")

    cur_avatar = _get_avatar(username)
    MAX_BYTES  = 15 * 1024 * 1024

    col_av, col_btns = st.columns([1, 4])
    with col_av:
        st.markdown(
            _avatar_circle_html(cur_avatar, size=88) +
            '<div style="height:8px"></div>',
            unsafe_allow_html=True)
    with col_btns:
        photo_file = st.file_uploader(
            t("photo_upload_label", lang),
            type=["jpg", "jpeg", "png", "webp"],
            key="pf_photo_upload")
        if photo_file:
            file_id = f"{photo_file.name}::{photo_file.size}"
            if st.session_state.get("_last_photo_saved") != file_id:
                raw_photo = photo_file.read()
                if len(raw_photo) > MAX_BYTES:
                    st.error(t("photo_too_large", lang))
                else:
                    suffix = Path(photo_file.name).suffix.lstrip(".")
                    save_user_avatar(username, raw_photo, suffix)
                    st.session_state["_last_photo_saved"] = file_id
                    st.session_state["_photo_msg"] = "saved"
                    st.rerun()
        if cur_avatar:
            if st.button(t("photo_remove", lang), key="pf_remove_photo"):
                remove_user_avatar(username)
                # Limpa avatar_v do profile em memória também
                st.session_state.user.get("profile", {}).pop("avatar_v", None)
                st.session_state.user["profile"] = {
                    k: v for k, v in st.session_state.user.get("profile", {}).items()
                    if k != "avatar_v"
                }
                st.session_state.pop("_last_photo_saved", None)
                st.session_state["_photo_msg"] = "removed"
                st.rerun()

    msg = st.session_state.pop("_photo_msg", None)
    if msg == "saved":
        st.success(t("photo_saved", lang))
    elif msg == "removed":
        st.success(t("photo_removed", lang))

    st.markdown("<hr style='border-color:#1a2535;margin:1.2rem 0;'>", unsafe_allow_html=True)

    # ---- Informações da Conta ----
    st.markdown(f"### {t('section_personal', lang)}")
    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input(t("full_name", lang), value=user.get("name", ""), key="set_name")
    with col2:
        new_email = st.text_input(t("email", lang), value=user.get("email", ""), key="set_email")
    st.markdown(
        f'<div style="font-size:.75rem;color:#4a5a6a;margin:-4px 0 10px;">'
        f'<b style="color:#6e7681;">{t("username_label", lang)}:</b> '
        f'<code style="background:#0f1824;padding:1px 6px;border-radius:4px;">{username}</code></div>',
        unsafe_allow_html=True)
    if st.button("💾 " + t("save", lang), key="save_personal"):
        ok = update_profile(username, {"name": new_name, "email": new_email})
        if ok:
            st.session_state.user["name"]  = new_name
            st.session_state.user["email"] = new_email
            st.success(t("data_saved", lang))
        else:
            st.error(t("save_error", lang))

    st.markdown("<hr style='border-color:#1a2535;margin:1.2rem 0;'>", unsafe_allow_html=True)

    # ---- Alterar Senha ----
    st.markdown(f"### {t('section_password', lang)}")
    col3, col4 = st.columns(2)
    with col3:
        new_pw  = st.text_input(t("new_password", lang),     type="password", key="set_newpw")
    with col4:
        conf_pw = st.text_input(t("confirm_password", lang), type="password", key="set_confpw")
    if st.button("🔒 " + t("change_password", lang), key="save_password"):
        if not new_pw or not conf_pw:
            st.error(t("pwd_fill_both", lang))
        elif new_pw != conf_pw:
            st.error(t("pwd_mismatch", lang))
        elif len(new_pw) < 6:
            st.error(t("pwd_too_short", lang))
        else:
            ok = update_password(username, new_pw)
            if ok:
                st.success(t("pwd_changed", lang))
            else:
                st.error(t("pwd_error", lang))

    st.markdown("<hr style='border-color:#1a2535;margin:1.2rem 0;'>", unsafe_allow_html=True)

    # ---- Perfil de aprendizado ----
    st.markdown(f"### {t('section_learning', lang)}")
    level_opts = ["Beginner","Pre-Intermediate","Intermediate","Advanced","Business English"]
    focus_opts = ["General Conversation","Business English","Travel","Academic",
                  "Pronunciation","Grammar","Vocabulary","Exam Prep"]

    cur_level = user.get("level","Beginner")
    cur_focus = user.get("focus","General Conversation")
    idx_l = level_opts.index(cur_level) if cur_level in level_opts else 0
    idx_f = focus_opts.index(cur_focus) if cur_focus in focus_opts else 0

    col5, col6 = st.columns(2)
    with col5:
        new_level = st.selectbox(t("english_level", lang), level_opts, index=idx_l, key="set_level")
    with col6:
        new_focus = st.selectbox(t("focus", lang), focus_opts, index=idx_f, key="set_focus")

    if st.button("💾 " + t("save", lang), key="save_level"):
        p = dict(profile)
        p["level"] = new_level
        p["focus"] = new_focus
        ok = update_profile(username, p)
        if ok:
            st.session_state.user["level"] = new_level
            st.session_state.user["focus"] = new_focus
            st.session_state.user["profile"] = p
            st.success(t("data_saved", lang))
        else:
            st.error(t("save_error", lang))

    st.markdown("<hr style='border-color:#1a2535;margin:1.2rem 0;'>", unsafe_allow_html=True)

    # ---- Idioma da interface + sotaque da IA ----
    st.markdown(f"### {t('section_lang', lang)}")
    lang_opts = {
        "Português (BR)": "pt-BR",
        "English (US)":   "en-US",
        "English (UK)":   "en-UK",
    }
    voice_opts = {
        "Português (BR) — pt-BR": "pt-BR",
        "English (US)   — en-US": "en-US",
        "English (UK)   — en-GB": "en-GB",
    }
    cur_lang_label  = next((k for k,v in lang_opts.items()  if v == lang), "Português (BR)")
    cur_voice       = profile.get("speech_lang", "en-US")
    cur_voice_label = next((k for k,v in voice_opts.items() if v == cur_voice), "English (US)   — en-US")

    col7, col8 = st.columns(2)
    with col7:
        new_lang_label  = st.selectbox(t("interface_lang", lang), list(lang_opts.keys()),
                                       index=list(lang_opts.keys()).index(cur_lang_label), key="set_lang")
    with col8:
        new_voice_label = st.selectbox(t("voice_lang", lang), list(voice_opts.keys()),
                                       index=list(voice_opts.keys()).index(cur_voice_label), key="set_voice")

    if st.button("💾 " + t("save", lang), key="save_lang"):
        p = dict(profile)
        p["language"]    = lang_opts[new_lang_label]
        p["speech_lang"] = voice_opts[new_voice_label]
        ok = update_profile(username, p)
        if ok:
            st.session_state.user["profile"] = p
            st.success(t("reload_lang", lang))
        else:
            st.error(t("save_error", lang))

    st.markdown("<hr style='border-color:#1a2535;margin:1.2rem 0;'>", unsafe_allow_html=True)

    # ---- Aparência — cores do anel e das bolhas ----
    st.markdown(f"### {t('section_appearance', lang)}")
    st.markdown(
        f'<p style="font-size:.75rem;color:#4a5a6a;margin:-8px 0 14px;">{t("appearance_hint", lang)}</p>',
        unsafe_allow_html=True)

    cur_ring = profile.get("ring_color",       "#f0a500")
    cur_user = profile.get("user_bubble_color", "#2d6a4f")
    cur_bot  = profile.get("bot_bubble_color",  "#1a1f2e")

    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        new_ring = st.color_picker(t("ring_color",        lang), value=cur_ring, key="cp_ring")
    with col_c2:
        new_user = st.color_picker(t("user_bubble_color", lang), value=cur_user, key="cp_user")
    with col_c3:
        new_bot  = st.color_picker(t("bot_bubble_color",  lang), value=cur_bot,  key="cp_bot")

    # Preview inline
    st.markdown(f"""
<div style="display:flex;gap:10px;margin:10px 0 14px;align-items:flex-end;">
    <div style="display:flex;flex-direction:column;align-items:center;gap:4px;">
        <div style="width:42px;height:42px;border-radius:50%;
                    background:#131c2a;
                    outline:2.5px solid {new_ring};
                    outline-offset:4px;
                    box-shadow:0 0 12px {new_ring}44;"></div>
        <span style="font-size:.58rem;color:#4a5a6a;">anel</span>
    </div>
    <div style="display:flex;flex-direction:column;gap:4px;flex:1;">
        <div style="align-self:flex-end;background:{new_user};
                    color:#fff;padding:6px 12px;border-radius:14px 14px 4px 14px;
                    font-size:.75rem;max-width:60%;">Você</div>
        <div style="align-self:flex-start;background:{new_bot};
                    color:#e6edf3;padding:6px 12px;border-radius:14px 14px 14px 4px;
                    border:1px solid #252d3d;font-size:.75rem;max-width:60%;">Professora</div>
    </div>
</div>""", unsafe_allow_html=True)

    if st.button("💾 " + t("save", lang), key="save_appearance"):
        p = dict(profile)
        p["ring_color"]        = new_ring
        p["user_bubble_color"] = new_user
        p["bot_bubble_color"]  = new_bot
        ok = update_profile(username, p)
        if ok:
            st.session_state.user["profile"] = p
            st.success(t("data_saved", lang))
        else:
            st.error(t("save_error", lang))

# =============================================================================
# TELA DE HISTORICO
# =============================================================================
def show_history() -> None:
    user     = st.session_state.user
    username = user["username"]
    profile  = user.get("profile", {})
    lang     = profile.get("language", "pt-BR")

    st.markdown("""<style>
.main .block-container{padding-top:1.5rem!important;}
</style>""", unsafe_allow_html=True)

    st.markdown(f"<h2 style='color:#e6edf3;margin-bottom:1rem;'>&#128196; {t('history',lang)}</h2>",
                unsafe_allow_html=True)

    convs = list_conversations(username)
    if not convs:
        st.markdown(f"<p style='color:#4a5a6a;'>{t('no_history',lang)}</p>",
                    unsafe_allow_html=True)
        return

    for conv in convs:
        cid   = conv["id"]
        title = conv.get("title") or conv.get("first_message","") or f"Conversa {cid[:8]}"
        date_ = conv.get("updated_at","") or conv.get("created_at","")
        msgs  = conv.get("msg_count", 0)

        c1, c2 = st.columns([5, 1])
        with c1:
            if st.button(
                f"&#9654; {title[:45]}{'...' if len(title)>45 else ''}",
                key=f"conv_{cid}", use_container_width=True,
            ):
                st.session_state.conv_id    = cid
                st.session_state["_vm_history"] = []
                st.session_state["_vm_reply"]   = ""
                st.session_state["_vm_user_said"] = ""
                st.session_state.page       = "voice"
                st.rerun()
            st.markdown(
                f"<div style='font-size:.65rem;color:#3a4e5e;margin-top:-6px;padding-left:4px;'>"
                f"&#128197; {date_[:16] if date_ else '---'} &middot; {msgs} msg</div>",
                unsafe_allow_html=True,
            )
        with c2:
            if st.button("&#128465;", key=f"del_{cid}", help=t("del_conv",lang)):
                delete_conversation(username, cid)
                if st.session_state.conv_id == cid:
                    st.session_state.conv_id = None
                st.rerun()

        st.markdown("<hr style='border:none;border-top:1px solid #1a2535;margin:4px 0;'/>",
                    unsafe_allow_html=True)

# =============================================================================
# DASHBOARD (professor)
# =============================================================================
def show_dashboard() -> None:
    user    = st.session_state.user
    profile = user.get("profile", {})
    lang    = profile.get("language", "pt-BR")

    st.markdown("""<style>
.main .block-container{padding-top:1.5rem!important;}
</style>""", unsafe_allow_html=True)

    st.markdown(f"<h2 style='color:#e6edf3;margin-bottom:1rem;'>&#128202; {t('dashboard',lang)}</h2>",
                unsafe_allow_html=True)

    stats = get_all_students_stats()
    if not stats:
        st.info("Nenhum aluno cadastrado ainda.")
        return

    # Resumo global
    total_students = len(stats)
    total_msgs     = sum(s.get("total_messages",0) for s in stats)
    total_convs    = sum(s.get("total_conversations",0) for s in stats)

    c1, c2, c3 = st.columns(3)
    def metric_card(col, icon, value, label):
        col.markdown(f"""
<div style="background:#0f1824;border:1px solid #1a2535;border-radius:14px;
     padding:16px;text-align:center;">
    <div style="font-size:1.6rem;">{icon}</div>
    <div style="font-size:1.5rem;font-weight:700;color:#f0a500;">{value}</div>
    <div style="font-size:.7rem;color:#4a5a6a;margin-top:2px;">{label}</div>
</div>""", unsafe_allow_html=True)

    metric_card(c1, "&#127891;", total_students, t("students", lang))
    metric_card(c2, "&#128172;", total_msgs,     t("total_msgs", lang))
    metric_card(c3, "&#128196;", total_convs,    t("conversations", lang))

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='color:#8b949e;font-size:.85rem;letter-spacing:.5px;margin-bottom:.5rem;'>"
                f"ALUNOS</h3>", unsafe_allow_html=True)

    for s in sorted(stats, key=lambda x: x.get("total_messages",0), reverse=True):
        name   = s.get("name","") or s.get("username","")
        uname  = s.get("username","")
        level  = s.get("level","—")
        focus  = s.get("focus","—")
        msgs   = s.get("total_messages",0)
        convs_ = s.get("total_conversations",0)
        last   = s.get("last_activity","")

        with st.expander(f"**{name}** ({uname}) — {level}"):
            col_a, col_b, col_c = st.columns(3)
            col_a.metric(t("total_msgs",lang),    msgs)
            col_b.metric(t("conversations",lang), convs_)
            col_c.metric("Foco", focus[:12] if focus else "—")
            if last:
                st.markdown(f"<small style='color:#4a5a6a;'>{t('last_activity',lang)}: {last[:16]}</small>",
                            unsafe_allow_html=True)

# =============================================================================
# ROUTER PRINCIPAL
# =============================================================================
def main():
    if not st.session_state.logged_in:
        _s = st.query_params.get("s", "")
        if _s and len(_s) > 10:
            _ud = validate_session(_s)
            if _ud:
                _un = _ud.get("_resolved_username") or next(
                    (k for k, v in load_students().items() if v["password"] == _ud["password"]), None
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

    token = st.session_state.get("_session_token", "")
    # Só seta o query param se ainda não estiver lá — evita loop
    if token and st.query_params.get("s") != token:
        st.query_params["s"] = token

    # Salva token apenas uma vez por sessão (não a cada rerun = -1 iframe)
    if token and not st.session_state.get("_session_saved"):
        js_save_session(token)
        st.session_state["_session_saved"] = True

    show_sidebar()
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