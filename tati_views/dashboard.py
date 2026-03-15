"""
pages/dashboard.py — Painel do professor.
Bug corrigido: lia 'total_messages' mas banco retornava 'messages' → agora padronizado.
"""

import streamlit as st
from database import get_all_students_stats
from ui_helpers import t
from guards.page_guard import page_guard, scroll_restore


@page_guard
def show_dashboard() -> None:
    profile = st.session_state.user.get("profile", {})
    lang    = profile.get("language", "pt-BR")

    # Restaura scroll
    scroll_restore()

    st.markdown("<div class='pav-page'>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:#e6edf3;margin-bottom:1rem;'>📊 {t('dashboard',lang)}</h2>",
                unsafe_allow_html=True)

    stats = get_all_students_stats()
    if not stats:
        st.info("Nenhum aluno cadastrado ainda.")
        return

    total_students = len(stats)
    total_msgs     = sum(s.get("total_messages", 0) for s in stats)       # ← chave corrigida
    total_convs    = sum(s.get("total_conversations", 0) for s in stats)  # ← chave corrigida

    c1, c2, c3 = st.columns(3)

    def metric_card(col, icon, value, label):
        col.markdown(f"""
<div style="background:#0f1824;border:1px solid #1a2535;border-radius:14px;
     padding:16px;text-align:center;">
    <div style="font-size:1.6rem;">{icon}</div>
    <div style="font-size:1.5rem;font-weight:700;color:#f0a500;">{value}</div>
    <div style="font-size:.7rem;color:#4a5a6a;margin-top:2px;">{label}</div>
</div>""", unsafe_allow_html=True)

    metric_card(c1, "🎓", total_students, t("students", lang))
    metric_card(c2, "💬", total_msgs,     t("total_msgs", lang))
    metric_card(c3, "📄", total_convs,    t("conversations", lang))

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#8b949e;font-size:.85rem;letter-spacing:.5px;margin-bottom:.5rem;'>ALUNOS</h3>",
                unsafe_allow_html=True)

    for s in sorted(stats, key=lambda x: x.get("total_messages", 0), reverse=True):
        name    = s.get("name", "") or s.get("username", "")
        uname   = s.get("username", "")
        level   = s.get("level", "—")
        focus   = s.get("focus", "—")
        msgs    = s.get("total_messages", 0)       # ← chave corrigida
        convs_  = s.get("total_conversations", 0)  # ← chave corrigida
        last    = s.get("last_activity", "")

        with st.expander(f"**{name}** ({uname}) — {level}"):
            col_a, col_b, col_c = st.columns(3)
            col_a.metric(t("total_msgs", lang),    msgs)
            col_b.metric(t("conversations", lang), convs_)
            col_c.metric("Foco", (focus[:12] if focus else "—"))
            if last:
                st.markdown(
                    f"<small style='color:#4a5a6a;'>{t('last_activity',lang)}: {last[:16]}</small>",
                    unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
