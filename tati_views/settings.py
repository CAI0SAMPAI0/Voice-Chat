"""
tati_views/settings.py — Tela de configurações do usuário.

Mudanças vs versão anterior:
─────────────────────────────
1. REMOVIDO inject_css('sidebar') — já injetado pelo inject_global_css()
   em app.py. Injetar duas vezes dobra o payload sem benefício.

2. REMOVIDO o bloco st.markdown(<style>...) inline (linhas 30-39).
   Aquele bloco sobrescrevia o settings.css externo com estilos
   duplicados. Toda a estilização agora vive em settings.css.

3. Preview de aparência usa classes semânticas (.set-bubble-preview,
   .set-bubble-user, .set-bubble-bot) em vez de style inline.
   As cores personalizadas do usuário continuam sendo aplicadas via
   style inline — mas APENAS para background/outline, não para layout.

4. Adicionado wrapper .set-avatar-col para substituir o seletor
   st-emotion-cache-* que quebrava a cada versão do Streamlit.

5. Adicionados .set-ring-preview e .set-color-label para o bloco
   de preview do anel, eliminando o seletor span[style="font-size:12px"].
"""

from pathlib import Path

import streamlit as st

from database import update_profile, update_password
from ui_helpers import (
    t, _get_avatar, _avatar_circle_html,
    save_user_avatar, remove_user_avatar,
    show_toast,
)
from guards.page_guard import page_guard, scroll_restore
from asset_loader import inject_css


@page_guard
def show_settings() -> None:
    user     = st.session_state.user
    username = user["username"]
    profile  = user.get("profile", {})
    lang     = profile.get("language", "pt-BR")

    scroll_restore()
    inject_css("settings")   # sidebar NÃO vai aqui — já vem do inject_global_css()

    st.markdown("<div class='pav-page'>", unsafe_allow_html=True)

    # ── Título ────────────────────────────────────────────────────────────────
    st.markdown(
        f"<h2 class='set-page-title'>⚙️ {t('settings', lang)}</h2>",
        unsafe_allow_html=True,
    )

    # ═════════════════════════════════════════════════════════════════════════
    # SEÇÃO: FOTO DE PERFIL
    # ═════════════════════════════════════════════════════════════════════════
    st.markdown(
        f"<h3 class='set-section-title'>{t('section_photo', lang)}</h3>",
        unsafe_allow_html=True,
    )

    cur_avatar = _get_avatar(username)
    MAX_BYTES  = 15 * 1024 * 1024

    col_av, col_btns = st.columns([1, 4])

    with col_av:
        # Wrapper com classe semântica — substitui o seletor st-emotion-cache-*
        st.markdown(
            "<div class='set-avatar-col'>"
            + _avatar_circle_html(cur_avatar, size=88)
            + "</div>",
            unsafe_allow_html=True,
        )

    with col_btns:
        photo_file = st.file_uploader(
            t("photo_upload_label", lang),
            type=["jpg", "jpeg", "png", "webp"],
            key="pf_photo_upload",
        )
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
                st.session_state.user["profile"] = {
                    k: v for k, v in st.session_state.user.get("profile", {}).items()
                    if k != "avatar_v"
                }
                st.session_state.pop("_last_photo_saved", None)
                st.session_state["_photo_msg"] = "removed"
                st.rerun()

    msg = st.session_state.pop("_photo_msg", None)
    if msg == "saved":
        show_toast(t("photo_saved", lang), type="success")
    elif msg == "removed":
        show_toast(t("photo_removed", lang), type="success")

    st.markdown("<hr class='set-divider'>", unsafe_allow_html=True)

    # ═════════════════════════════════════════════════════════════════════════
    # SEÇÃO: INFORMAÇÕES DA CONTA
    # ═════════════════════════════════════════════════════════════════════════
    st.markdown(
        f"<h3 class='set-section-title'>{t('section_personal', lang)}</h3>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input(
            t("full_name", lang), value=user.get("name", ""), key="set_name"
        )
    with col2:
        new_email = st.text_input(
            t("email", lang), value=user.get("email", ""), key="set_email"
        )

    st.markdown(
        f"<p class='set-username-row'>"
        f"<b style='color:var(--text-secondary);'>{t('username_label', lang)}:</b>"
        f" <code>{username}</code></p>",
        unsafe_allow_html=True,
    )

    if st.button(f"💾 {t('save', lang)}", key="save_personal"):
        ok = update_profile(username, {"name": new_name, "email": new_email})
        if ok:
            st.session_state.user["name"]  = new_name
            st.session_state.user["email"] = new_email
            show_toast(t("data_saved", lang), type="success")
        else:
            st.error(t("save_error", lang))

    st.markdown("<hr class='set-divider'>", unsafe_allow_html=True)

    # ═════════════════════════════════════════════════════════════════════════
    # SEÇÃO: ALTERAR SENHA
    # ═════════════════════════════════════════════════════════════════════════
    st.markdown(
        f"<h3 class='set-section-title'>{t('section_password', lang)}</h3>",
        unsafe_allow_html=True,
    )

    col3, col4 = st.columns(2)
    with col3:
        new_pw  = st.text_input(
            t("new_password", lang), type="password", key="set_newpw"
        )
    with col4:
        conf_pw = st.text_input(
            t("confirm_password", lang), type="password", key="set_confpw"
        )

    if st.button(f"🔒 {t('change_password', lang)}", key="save_password"):
        if not new_pw or not conf_pw:
            st.error(t("pwd_fill_both", lang))
        elif new_pw != conf_pw:
            st.error(t("pwd_mismatch", lang))
        elif len(new_pw) < 6:
            st.error(t("pwd_too_short", lang))
        else:
            ok = update_password(username, new_pw)
            if ok:
                show_toast(t("pwd_changed", lang), type="success")
            else:
                st.error(t("pwd_error", lang))

    st.markdown("<hr class='set-divider'>", unsafe_allow_html=True)

    # ═════════════════════════════════════════════════════════════════════════
    # SEÇÃO: PERFIL DE APRENDIZADO
    # ═════════════════════════════════════════════════════════════════════════
    st.markdown(
        f"<h3 class='set-section-title'>{t('section_learning', lang)}</h3>",
        unsafe_allow_html=True,
    )

    level_opts = [
        "Beginner", "Pre-Intermediate", "Intermediate",
        "Advanced", "Business English",
    ]
    focus_opts = [
        "General Conversation", "Business English", "Travel", "Academic",
        "Pronunciation", "Grammar", "Vocabulary", "Exam Prep",
    ]

    cur_level = user.get("level", "Beginner")
    cur_focus = user.get("focus", "General Conversation")
    idx_l = level_opts.index(cur_level) if cur_level in level_opts else 0
    idx_f = focus_opts.index(cur_focus) if cur_focus in focus_opts else 0

    col5, col6 = st.columns(2)
    with col5:
        new_level = st.selectbox(
            t("english_level", lang), level_opts, index=idx_l, key="set_level"
        )
    with col6:
        new_focus = st.selectbox(
            t("focus", lang), focus_opts, index=idx_f, key="set_focus"
        )

    if st.button(f"💾 {t('save', lang)}", key="save_level"):
        p = dict(profile)
        p["level"] = new_level
        p["focus"] = new_focus
        ok = update_profile(username, p)
        if ok:
            st.session_state.user["level"]   = new_level
            st.session_state.user["focus"]   = new_focus
            st.session_state.user["profile"] = p
            show_toast(t("data_saved", lang), type="success")
        else:
            st.error(t("save_error", lang))

    st.markdown("<hr class='set-divider'>", unsafe_allow_html=True)

    # ═════════════════════════════════════════════════════════════════════════
    # SEÇÃO: IDIOMA DA INTERFACE
    # ═════════════════════════════════════════════════════════════════════════
    st.markdown(
        f"<h3 class='set-section-title'>{t('section_lang', lang)}</h3>",
        unsafe_allow_html=True,
    )

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

    cur_lang_label  = next(
        (k for k, v in lang_opts.items()  if v == lang), "Português (BR)"
    )
    cur_voice       = profile.get("speech_lang", "en-US")
    cur_voice_label = next(
        (k for k, v in voice_opts.items() if v == cur_voice),
        "English (US)   — en-US",
    )

    col7, col8 = st.columns(2)
    with col7:
        new_lang_label = st.selectbox(
            t("interface_lang", lang),
            list(lang_opts.keys()),
            index=list(lang_opts.keys()).index(cur_lang_label),
            key="set_lang",
        )
    with col8:
        new_voice_label = st.selectbox(
            t("voice_lang", lang),
            list(voice_opts.keys()),
            index=list(voice_opts.keys()).index(cur_voice_label),
            key="set_voice",
        )

    if st.button(f"💾 {t('save', lang)}", key="save_lang"):
        p = dict(profile)
        p["language"]    = lang_opts[new_lang_label]
        p["speech_lang"] = voice_opts[new_voice_label]
        ok = update_profile(username, p)
        if ok:
            st.session_state.user["profile"] = p
            show_toast(t("reload_lang", lang), type="success")
        else:
            st.error(t("save_error", lang))

    st.markdown("<hr class='set-divider'>", unsafe_allow_html=True)

    # ═════════════════════════════════════════════════════════════════════════
    # SEÇÃO: APARÊNCIA
    # ═════════════════════════════════════════════════════════════════════════
    st.markdown(
        f"<h3 class='set-section-title'>{t('section_appearance', lang)}</h3>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p class='set-hint'>{t('appearance_hint', lang)}</p>",
        unsafe_allow_html=True,
    )

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

    # Preview de aparência — usa classes semânticas do settings.css
    # As cores personalizadas são aplicadas via style inline APENAS
    # em background/outline, nunca em layout (margin, padding, width).
    st.markdown(f"""
<div class="set-bubble-preview">
    <div class="set-ring-preview">
        <div class="set-ring-circle"
             style="outline:3px solid {new_ring};
                    outline-offset:4px;
                    box-shadow:0 0 14px {new_ring}55;">
        </div>
        <span class="set-color-label">anel</span>
    </div>
    <div class="set-bubbles-col">
        <div class="set-bubble-user"
             style="background:{new_user};">
            {t("you", lang) if t("you", lang) != "you" else "Você"}
        </div>
        <div class="set-bubble-bot"
             style="background:{new_bot};">
            {PROF_NAME_SHORT}
        </div>
    </div>
</div>""", unsafe_allow_html=True)

    if st.button(f"💾 {t('save', lang)}", key="save_appearance"):
        p = dict(profile)
        p["ring_color"]        = new_ring
        p["user_bubble_color"] = new_user
        p["bot_bubble_color"]  = new_bot
        ok = update_profile(username, p)
        if ok:
            st.session_state.user["profile"] = p
            show_toast(t("data_saved", lang), type="success")
        else:
            st.error(t("save_error", lang))

    st.markdown("</div>", unsafe_allow_html=True)  # fecha .pav-page


# Constante usada no preview — evita importar PROF_NAME de ui_helpers
# duas vezes (já importado via t())
import os as _os
PROF_NAME_SHORT = _os.getenv("PROFESSOR_NAME", "Teacher Tati").split()[0]