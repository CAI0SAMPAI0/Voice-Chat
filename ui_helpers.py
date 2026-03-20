import os
import base64
import json
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

from database import (
    delete_session, new_conversation,
    get_user_avatar_db, save_user_avatar_db, remove_user_avatar_db,
)

# CONSTANTES
PROF_NAME  = os.getenv("PROFESSOR_NAME", "Teacher Tati")
PHOTO_PATH = os.getenv("PROFESSOR_PHOTO", "assets/professor.jpg")
_ASSETS    = Path(__file__).resolve().parent / "assets"


# LOADERS DE ASSET

def load_css(filename: str) -> str:
    """Lê assets/css/<filename> e devolve uma tag <style>."""
    path = _ASSETS / "css" / filename
    return f"<style>{path.read_text(encoding='utf-8')}</style>" if path.exists() else ""


def load_js(filename: str) -> str:
    """Lê assets/js/<filename> e devolve uma tag <script>."""
    path = _ASSETS / "js" / filename
    return f"<script>{path.read_text(encoding='utf-8')}</script>" if path.exists() else ""


def load_html(filename: str, **vars_) -> str:
    """
    Lê assets/html/<filename> e substitui {{CHAVE}} pelos valores em vars_.
    Exemplo: load_html("avatar_card.html", PROF_NAME="Teacher Tati")
    """
    path = _ASSETS / "html" / filename
    if not path.exists():
        return ""
    html = path.read_text(encoding="utf-8")
    for key, val in vars_.items():
        html = html.replace(f"{{{{{key}}}}}", str(val))
    return html


def inject_global_css():
    """Injeta global.css + sidebar.css em todas as páginas."""
    st.markdown(load_css("global.css"),  unsafe_allow_html=True)
    st.markdown(load_css("sidebar.css"), unsafe_allow_html=True)


# I18N
_STRINGS = {
    "pt-BR": {
        "username": "Usuário", "password": "Senha",
        "enter": "Entrar", "create_account": "Criar Conta",
        "full_name": "Nome completo", "email": "E-mail",
        "logout": "Sair", "settings": "Configurações",
        "history": "Histórico", "dashboard": "Painel",
        "voice_mode": "Modo Voz", "new_conv": "Nova conversa de voz",
        "del_conv": "Excluir", "tap_to_speak": "Toque para falar",
        "tap_to_stop": "Toque para parar", "processing": "Processando...",
        "speaking_ai": "Falando...", "save": "Salvar",
        "english_level": "Nível de inglês", "focus": "Foco",
        "interface_lang": "Idioma da interface", "voice_lang": "Sotaque da IA (voz)",
        "change_password": "Alterar senha", "new_password": "Nova senha",
        "confirm_password": "Confirmar senha", "cancel": "Cancelar",
        "students": "Alunos", "total_msgs": "Mensagens",
        "conversations": "Conversas", "last_activity": "Última atividade",
        "no_history": "Nenhuma conversa ainda.",
        "error_api": "Erro ao chamar a IA.", "error_mic": "Erro no microfone.",
        "section_photo": "📸 Foto de Perfil",
        "photo_upload_label": "Alterar foto — JPG, PNG ou WEBP (máx 15 MB)",
        "photo_remove": "🗑️ Remover foto", "photo_saved": "✅ Foto salva!",
        "photo_removed": "Foto removida.", "photo_too_large": "❌ Foto muito grande. Máximo 15 MB.",
        "section_personal": "👤 Informações da Conta", "username_label": "Usuário",
        "section_password": "🔒 Alterar Senha",
        "pwd_fill_both": "Preencha os dois campos.", "pwd_mismatch": "As senhas não coincidem.",
        "pwd_too_short": "Mínimo 6 caracteres.", "pwd_changed": "✅ Senha alterada!",
        "pwd_error": "Erro ao alterar senha.", "data_saved": "✅ Dados atualizados!",
        "save_error": "Erro ao salvar.", "section_learning": "🎓 Perfil de Aprendizado",
        "section_lang": "🌐 Idioma da Interface",
        "reload_lang": "Salvo! Recarregue para ver o novo idioma.",
        "section_appearance": "🎨 Aparência",
        "ring_color": "Cor do anel", "user_bubble_color": "Sua bolha",
        "bot_bubble_color": "Bolha da IA",
        "appearance_hint": "As cores aparecem imediatamente no modo conversa.",
    },
    "en-US": {
        "username": "Username", "password": "Password",
        "enter": "Sign In", "create_account": "Create Account",
        "full_name": "Full name", "email": "E-mail",
        "logout": "Log out", "settings": "Settings",
        "history": "History", "dashboard": "Dashboard",
        "voice_mode": "Voice Mode", "new_conv": "New voice chat",
        "del_conv": "Delete", "tap_to_speak": "Tap to speak",
        "tap_to_stop": "Tap to stop", "processing": "Processing...",
        "speaking_ai": "Speaking...", "save": "Save",
        "english_level": "English level", "focus": "Focus",
        "interface_lang": "Interface language", "voice_lang": "AI voice accent",
        "change_password": "Change password", "new_password": "New password",
        "confirm_password": "Confirm password", "cancel": "Cancel",
        "students": "Students", "total_msgs": "Messages",
        "conversations": "Conversations", "last_activity": "Last activity",
        "no_history": "No conversations yet.",
        "error_api": "Error calling AI.", "error_mic": "Microphone error.",
        "section_photo": "📸 Profile Photo",
        "photo_upload_label": "Change photo — JPG, PNG or WEBP (max 15 MB)",
        "photo_remove": "🗑️ Remove photo", "photo_saved": "✅ Photo saved!",
        "photo_removed": "Photo removed.", "photo_too_large": "❌ Photo too large. Maximum 15 MB.",
        "section_personal": "👤 Account Information", "username_label": "Username",
        "section_password": "🔒 Change Password",
        "pwd_fill_both": "Please fill in both fields.", "pwd_mismatch": "Passwords do not match.",
        "pwd_too_short": "Minimum 6 characters.", "pwd_changed": "✅ Password changed!",
        "pwd_error": "Error changing password.", "data_saved": "✅ Data updated!",
        "save_error": "Error saving.", "section_learning": "🎓 Learning Profile",
        "section_lang": "🌐 Interface Language",
        "reload_lang": "Saved! Reload to see the new language.",
        "section_appearance": "🎨 Appearance",
        "ring_color": "Ring colour", "user_bubble_color": "Your bubble",
        "bot_bubble_color": "AI bubble",
        "appearance_hint": "Colours apply instantly in conversation mode.",
    },
}

def t(key: str, lang: str = "pt-BR") -> str:
    return _STRINGS.get(lang, _STRINGS["pt-BR"]).get(key, key)

# FOTO / AVATAR (com cache)

@st.cache_data(ttl=300)
def get_photo_b64() -> str | None:
    p = Path(PHOTO_PATH)
    if p.exists():
        ext  = p.suffix.lower().replace(".", "")
        mime = "jpeg" if ext in ("jpg", "jpeg") else ext
        return f"data:image/{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"
    return None

@st.cache_data(ttl=300)
def get_tati_mini_b64() -> str:
    for _p in [Path("assets/tati.png"), Path("assets/tati.jpg")]:
        if _p.exists():
            _ext  = _p.suffix.lstrip(".").lower()
            _mime = "jpeg" if _ext in ("jpg", "jpeg") else _ext
            return f"data:image/{_mime};base64,{base64.b64encode(_p.read_bytes()).decode()}"
    return get_photo_b64() or ""

@st.cache_data(ttl=300)
def get_avatar_frames() -> dict:
    _cwd = Path(os.getcwd()).resolve()
    def _load(filename: str) -> str:
        for base in [_cwd, Path(__file__).resolve().parent]:
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

@st.cache_data(ttl=60)
def _get_avatar(username: str) -> str | None:
    result = get_user_avatar_db(username)
    if not result:
        return None
    raw, mime = result
    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"

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

# HELPER: monta a tela de voz a partir do template HTML

def _rgba(h: str, a: float) -> str:
    h = h.lstrip("#")
    if len(h) == 3: h = h[0]*2 + h[1]*2 + h[2]*2
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{a})"

def build_voice_html(user: dict, history: list, tts_b64: str, vm_error: str) -> str:
    """Monta o HTML completo da tela de voz usando template + JS/CSS externos."""
    profile = user.get("profile", {})
    lang    = profile.get("language", "pt-BR")

    ring_color        = profile.get("ring_color",        "#f0a500")
    user_bubble_color = profile.get("user_bubble_color", "#2d6a4f")
    bot_bubble_color  = profile.get("bot_bubble_color",  "#1a1f2e")

    frames  = get_avatar_frames()
    strings = {
        "profName":   PROF_NAME,
        "tapSpeak":   t("tap_to_speak", lang),
        "tapStop":    t("tap_to_stop",  lang),
        "speaking":   t("speaking_ai",  lang),
        "processing": t("processing",   lang),
    }

    voice_css_path = _ASSETS / "css" / "voice.css"
    voice_css      = voice_css_path.read_text(encoding="utf-8") if voice_css_path.exists() else ""

    return load_html(
        "voice_screen.html",
        RING_COLOR        = ring_color,
        RING_COLOR_DIM    = _rgba(ring_color, 0.12),
        RING_COLOR_GLOW   = _rgba(ring_color, 0.25),
        USER_BUBBLE_COLOR = user_bubble_color,
        BOT_BUBBLE_COLOR  = bot_bubble_color,
        VOICE_CSS         = voice_css,
        AUDIO_CONTROLS_EXTRA = "",
        FRAMES_JSON       = json.dumps(frames),
        STRINGS_JSON      = json.dumps(strings),
        GOOD_PRONUNC      = "true" if st.session_state.get("_vm_good_pronunciation") else "false",
        HISTORY_JSON      = json.dumps(history),
        TTS_B64_JSON      = json.dumps(tts_b64),
        VM_ERROR_JSON     = json.dumps(vm_error),
        AUDIO_JS          = load_js("audio.js"),
        AVATAR_JS         = load_js("avatar.js"),
        MIC_JS            = load_js("mic.js"),
    )


# SESSION
SESSION_DEFAULTS = {
    "logged_in": False, "user": None, "page": "voice",
    "conv_id": None, "audio_key": 0,
    "_vm_history": [], "_vm_reply": "", "_vm_tts_b64": "",
    "_vm_user_said": "", "_vm_error": "", "_vm_last_upload": None,
}

def init_session():
    for k, v in SESSION_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _js_run(filename: str, **vars_) -> None:
    """Roda um JS externo dentro de um iframe mínimo."""
    path = _ASSETS / "js" / filename
    if not path.exists():
        return
    js = path.read_text(encoding="utf-8")
    for key, val in vars_.items():
        js = js.replace(f"{{{{{key}}}}}", str(val))
    components.html(
        f"<!DOCTYPE html><html><head>"
        f"<style>html,body{{margin:0;padding:0;overflow:hidden;}}</style>"
        f"</head><body><script>{js}</script></body></html>",
        height=1,
    )


def _logout():
    token = st.session_state.get("_session_token", "")
    if token:
        delete_session(token)
    _js_run("session.js", TOKEN_VALUE="", ACTION="clear")
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    for k, v in SESSION_DEFAULTS.items():
        st.session_state[k] = v
    st.session_state.pop("_session_saved", None)
    st.session_state.pop("_cookie_checked", None)


def js_save_session(token: str) -> None:
    _js_run("session.js", TOKEN_VALUE=token, ACTION="save")

def js_auto_login() -> None:
    _js_run("session.js", TOKEN_VALUE="", ACTION="auto")

def js_toggle_sidebar() -> None:
    _js_run("sidebar.js")


# TOAST NOTIFICATIONS

def show_toast(message: str, type: str = "success") -> None:
    """Exibe um toast no canto superior direito."""
    bg = "#2d6a4f" if type == "success" else "#e05c2a"
    js = f"""
    (function(){{
      var doc = window.parent ? window.parent.document : document;
      var root = doc.getElementById('pav-toast-root');
      if(!root) {{
        root = doc.createElement('div');
        root.id = 'pav-toast-root';
        root.style.position = 'fixed';
        root.style.top = '16px';
        root.style.right = '16px';
        root.style.zIndex = '99999';
        root.style.display = 'flex';
        root.style.flexDirection = 'column';
        root.style.gap = '8px';
        doc.body.appendChild(root);
      }}
      var el = doc.createElement('div');
      el.textContent = {json.dumps(message)};
      el.style.background = '{bg}';
      el.style.color = '#fff';
      el.style.padding = '10px 14px';
      el.style.borderRadius = '8px';
      el.style.fontSize = '.78rem';
      el.style.boxShadow = '0 4px 16px rgba(0,0,0,0.35)';
      el.style.maxWidth = '260px';
      el.style.fontFamily = 'system-ui,-apple-system,Segoe UI,Roboto,sans-serif';
      root.appendChild(el);
      setTimeout(function(){{
        el.style.transition = 'opacity .3s ease, transform .3s ease';
        el.style.opacity = '0';
        el.style.transform = 'translateY(-4px)';
        setTimeout(function(){{ if(el.parentNode) el.parentNode.removeChild(el); }}, 320);
      }}, 2600);
    }})();
    """
    components.html(
        f"<!DOCTYPE html><html><body><script>{js}</script></body></html>",
        height=0,
    )


def get_or_create_conv(username: str) -> str:
    from database import list_conversations
    if st.session_state.conv_id:
        return st.session_state.conv_id
    convs = list_conversations(username)
    cid   = convs[0]["id"] if convs else new_conversation(username)
    st.session_state.conv_id = cid
    return cid

# SIDEBAR

def show_sidebar() -> None:
    user     = st.session_state.user
    username = user["username"]
    profile  = user.get("profile", {})
    lang     = profile.get("language", "pt-BR")
    page     = st.session_state.page

    js_toggle_sidebar()

    with st.sidebar:
        uav_html = user_avatar_html(username, size=62)
        st.markdown(f"""
<div class="sb-user-row" id="user_avatar">
    {uav_html}
    <div>
        <div class="sb-user-name">{user.get('name','').split()[0]}</div>
        <div class="sb-user-status">&#9679; Online</div>
    </div>
</div>
<hr style="border:none;border-top:1px solid var(--border-subtle);margin:0 0 14px;"/>
""", unsafe_allow_html=True)

        nav_items = [
            ("voice",    f"🎙️ {t('voice_mode', lang)}"),
            ("settings", f"⚙️ {t('settings',   lang)}"),
            ("history",  f"📄 {t('history',    lang)}"),
        ]
        if user.get("role") in ("professor", "programador", "professora", "Professora", "Tatiana", "Tati"):
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
                for k in ["_vm_history","_vm_reply","_vm_tts_b64","_vm_user_said","_vm_error","_vm_last_upload"]:
                    st.session_state.pop(k, None)
                st.session_state["_vm_history"] = []
                st.rerun()

        st.markdown("<hr style='border:none;border-top:1px solid var(--border-subtle);margin:10px 0;'/>",
                    unsafe_allow_html=True)
        st.markdown(f"""
<div style="padding:4px 4px 0;font-size:.72rem;color:var(--text-muted);line-height:2;">
    <b style="color:var(--text-secondary);">{user.get('name','')}</b><br>
    {user.get('level','—')} &middot; {user.get('focus','—')}
</div>""", unsafe_allow_html=True)

        st.markdown("""<div style="flex:1;min-height:24px;"></div>
<hr style="border:none;border-top:1px solid var(--border-subtle);margin:0 0 10px;"/>""",
                    unsafe_allow_html=True)

        if st.button(f"🚪 {t('logout', lang)}", use_container_width=True,
                     key="sb_logout", type="secondary"):
            _logout()
            st.rerun()