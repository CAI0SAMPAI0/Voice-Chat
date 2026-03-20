import streamlit as st
import anthropic
import os
from datetime import datetime, date
from database import (
    get_all_students_stats,
    load_conversation,
    load_students,
    list_conversations,
    update_profile,
)
from ui_helpers import t
from guards.page_guard import page_guard, scroll_restore
from asset_loader import inject_css

# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_api_key() -> str:
    for k in ["ANTHROPIC_API_KEY"] + [f"ANTHROPIC_API_KEY_{i}" for i in range(1, 5)]:
        v = os.getenv(k, "")
        if v: return v
    try:
        return st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        return ""


def _days_inactive(last_activity: str):
    if not last_activity or last_activity in ("---", ""):
        return None
    try:
        last = datetime.fromisoformat(last_activity[:19]).date()
        return (date.today() - last).days
    except Exception:
        return None


def _student_status(msgs: int, last_activity: str, lang: str) -> tuple[str, str]:
    if msgs == 0:
        return ("Novo" if lang == "pt-BR" else "New"), "#c084fc"
    days = _days_inactive(last_activity)
    if days is None or days <= 5:
        return ("Saudável" if lang == "pt-BR" else "Active"), "#4ade80"
    if days <= 10:
        txt = f"Atenção · {days}d" if lang == "pt-BR" else f"Warning · {days}d"
        return txt, "#f0a500"
    txt = f"Inativo · {days}d" if lang == "pt-BR" else f"Inactive · {days}d"
    return txt, "#ff7a5c"


def _extract_errors_and_hits(msgs: list) -> tuple[list, list]:
    error_kws = [
        ("Quick check", "grammar"), ("we say",    "grammar"),
        ("instead of",  "grammar"), ("should be", "grammar"),
        ("Try saying",  "pronunc."), ("not quite", "grammar"),
        ("missing",     "grammar"), ("incorrect", "grammar"),
    ]
    hit_kws = [
        "great pronunciation", "excellent", "perfect", "well done",
        "spot on", "nailed it", "beautifully", "very clear",
        "ótima pronúncia", "perfeito", "muito bem", "excelente",
    ]
    errors, hits = [], []
    for m in msgs:
        if m.get("role") != "assistant": continue
        c, cl = m.get("content", ""), m.get("content", "").lower()
        for kw, etype in error_kws:
            if kw.lower() in cl:
                for sent in c.replace("\n", " ").split(". "):
                    if kw.lower() in sent.lower() and len(sent) > 10:
                        errors.append({"type": etype, "text": sent.strip()[:120]})
                        break
                break
        for kw in hit_kws:
            if kw in cl:
                for sent in c.replace("\n", " ").split(". "):
                    if kw in sent.lower() and len(sent) > 8:
                        hits.append(sent.strip()[:100])
                        break
                break
    seen_e, seen_h = set(), set()
    ue = [e for e in errors if not (e["text"] in seen_e or seen_e.add(e["text"]))]
    uh = [h for h in hits   if not (h in seen_h or seen_h.add(h))]
    return ue[:5], uh[:3]


def _get_ai_insight(student: dict, convs: list, custom_prompt: str = "") -> tuple[str, str]:
    """Retorna (texto, erro). erro='' se OK, texto='' se falhou."""
    try:
        api_key = _get_api_key()
        if not api_key:
            return "", "API key não encontrada. Verifique ANTHROPIC_API_KEY no .env"
        sample = convs[-30:]
        convo  = "\n".join(
            f"{'Aluno' if m['role']=='user' else 'Teacher'}: {m.get('content','')[:200]}"
            for m in sample if m.get("content")
        )
        if not convo.strip():
            return "", "Sem histórico de conversa para analisar."
        prompt = (
            f"Analise este aluno de inglês e escreva UM parágrafo curto (máximo 3 frases) "
            f"com: 1 ponto forte, 1 dificuldade e 1 sugestão prática. Sem títulos.\n\n"
            f"Aluno: {student.get('name','')} | Nível: {student.get('level','')} | "
            f"Foco: {student.get('focus','')} | Msgs: {student.get('total_messages',0)}\n"
        )
        if custom_prompt:
            prompt += f"Instrução do professor: {custom_prompt}\n"
        prompt += f"\nConversa:\n{convo}"
        client = anthropic.Anthropic(api_key=api_key)
        resp   = client.messages.create(
            model="claude-haiku-4-5-20251001", max_tokens=450,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip(), ""
    except Exception as e:
        return "", str(e)


# ── Wrappers com classe CSS por contexto ──────────────────────────────────────

def _btn(css_class: str, label: str, key: str, **kwargs) -> bool:
    st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
    clicked = st.button(label, key=key, **kwargs)
    st.markdown('</div>', unsafe_allow_html=True)
    return clicked

def _select(css_class: str, label: str, options: list, **kwargs):
    st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
    val = st.selectbox(label, options, **kwargs)
    st.markdown('</div>', unsafe_allow_html=True)
    return val

def _textarea(css_class: str, label: str, **kwargs):
    st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
    val = st.text_area(label, **kwargs)
    st.markdown('</div>', unsafe_allow_html=True)
    return val


# ── Dashboard ─────────────────────────────────────────────────────────────────

@page_guard
def show_dashboard() -> None:
    profile = st.session_state.user.get("profile", {})
    lang    = profile.get("language", "pt-BR")

    scroll_restore()
    inject_css("dashboard", "dashboard_pedagogico")

    st.markdown("""<style>
    .btn-action    button { background:#2563eb !important; color:#fff !important; }
    .btn-danger    button { background:#dc2626 !important; color:#fff !important; }
    .btn-secondary button { opacity:.75; }

    .m-grid { display:flex; gap:.8rem; flex-wrap:wrap; margin-bottom:1.2rem; }
    .m-card {
        flex:1; min-width:130px; background:#0d1526;
        border:1px solid #1a2535; border-radius:12px;
        padding:.9rem 1rem; text-align:center;
    }
    .m-icon { font-size:1.2rem; }
    .m-val  { font-size:1.7rem; font-weight:700; color:#e2e8f0; margin:.2rem 0 0; }
    .m-lbl  { font-size:.7rem; color:#4a5a6a; text-transform:uppercase;
               letter-spacing:.5px; margin:0; }

    .tag-err {
        display:inline-block; background:rgba(224,92,42,.12); color:#ff7a5c;
        border:1px solid rgba(224,92,42,.3); border-radius:12px;
        padding:2px 8px; font-size:.68rem; margin-right:4px;
    }
    .tag-hit {
        display:inline-block; background:rgba(74,222,128,.1); color:#4ade80;
        border:1px solid rgba(74,222,128,.3); border-radius:12px;
        padding:2px 8px; font-size:.7rem; margin:2px 2px 2px 0;
    }
    .ins-box {
        background:rgba(139,92,246,.07); border:1px solid rgba(139,92,246,.3);
        border-left:3px solid #8b5cf6; border-radius:10px;
        padding:.8rem 1rem; font-size:.83rem; color:#c084fc;
        font-style:italic; line-height:1.55; margin:.4rem 0 .8rem;
    }
    .ins-label {
        font-size:.68rem; font-weight:700; text-transform:uppercase;
        letter-spacing:.4px; display:block; margin-bottom:4px; color:#8b5cf6;
    }

    /* Classes de markdown controladas pelo CSS externo */
    .db-page-title   { font-size:1.5rem; font-weight:700; color:#e6edf3; margin:0 0 1.2rem; }
    .db-divider      { border:none; border-top:1px solid #1a2535; margin:1rem 0; }
    .db-divider-soft { border:none; border-top:1px solid #0f1824; margin:.5rem 0; }
    .section-tip     { font-size:.75rem; color:#4a5a6a; margin:0 0 .8rem; }
    .db-empty-hint   { font-size:.75rem; color:#4a5a6a; font-style:italic; }
    .db-meta-txt     { font-size:.75rem; color:#8b949e; line-height:1.8; margin:.2rem 0 .6rem; }
    </style>""", unsafe_allow_html=True)

    BR = lang == "pt-BR"
    L = {
        "title":        "Dashboard Pedagógico"          if BR else "Pedagogical Dashboard",
        "students":     "Alunos"                        if BR else "Students",
        "messages":     "Mensagens"                     if BR else "Messages",
        "errors":       "Erros"                         if BR else "Errors",
        "corrections":  "Correções"                     if BR else "Corrections",
        "insights":     "📊 Insights da Turma"          if BR else "📊 Class Insights",
        "corr_rate":    "Taxa de Correção"               if BR else "Correction Rate",
        "total_err":    "Total de Erros"                if BR else "Total Errors",
        "err_types":    "Tipos de Erro"                 if BR else "Error Types",
        "msgs_std":     "Msgs/Aluno"                    if BR else "Msgs/Student",
        "section_tip":  "Clique no aluno para expandir" if BR else "Click to expand",
        "focus":        "Foco"                          if BR else "Focus",
        "last_act":     "Última atividade"              if BR else "Last activity",
        "errors_lbl":   "Erros"                         if BR else "Errors",
        "hits_lbl":     "Acertos"                       if BR else "Hits",
        "no_errs_s":    "Nenhum erro registrado."       if BR else "No errors recorded.",
        "no_hits":      "Nenhum acerto registrado."     if BR else "No hits recorded.",
        "ai_insight":   "✨ AI Insight",
        "gen_insight":  "✨ Gerar Insight"               if BR else "✨ Generate Insight",
        "analyzing":    "Analisando..."                 if BR else "Analyzing...",
        "chg_level":    "Nível"                         if BR else "Level",
        "level_saved":  "✅ Nível atualizado!"          if BR else "✅ Level updated!",
        "cust_prompt":  "🎯 Prompt personalizado"       if BR else "🎯 Custom prompt",
        "prompt_hint":  "Ex: Foque em passado simples"  if BR else "E.g.: Focus on past simple",
        "prompt_saved": "✅ Prompt salvo!"              if BR else "✅ Prompt saved!",
        "manage":       "⚙️ Gerenciamento de Alunos"    if BR else "⚙️ Student Management",
        "select_std":   "Selecionar aluno"              if BR else "Select student",
        "remove":       "🗑 Remover"                    if BR else "🗑 Remove",
        "confirm_rem":  "Tem certeza? Irreversível."    if BR else "Are you sure? Irreversible.",
        "confirm":      "✅ Confirmar"                  if BR else "✅ Confirm",
        "cancel":       "❌ Cancelar"                   if BR else "❌ Cancel",
        "removed_ok":   "removido com sucesso."         if BR else "removed successfully.",
        "summary":      "📈 Resumo da Turma"            if BR else "📈 Class Summary",
        "avg":          "em média"                      if BR else "on average",
        "most_active":  "Aluno mais ativo"              if BR else "Most active student",
        "save":         "💾 Salvar"                     if BR else "💾 Save",
        "no_students":  "Nenhum aluno cadastrado ainda." if BR else "No students registered yet.",
        "no_conv":      "Sem conversa suficiente para gerar insight." if BR else "Not enough conversation history.",
    }

    # ── Dados ─────────────────────────────────────────────────────────────────
    stats     = get_all_students_stats()
    all_users = load_students()
    stats     = [s for s in stats if all_users.get(s["username"], {}).get("role") == "student"]

    # Título via markdown com classe
    st.markdown(f"<h2 class='db-page-title'>🎓 {L['title']}</h2>", unsafe_allow_html=True)

    if not stats:
        st.info(L["no_students"])
        return

    total_students = len(stats)
    total_msgs     = sum(s.get("total_messages", 0) for s in stats)
    total_fixes    = sum(s.get("corrections", 0) for s in stats)
    corr_rate      = round(total_fixes / total_msgs * 100, 1) if total_msgs > 0 else 0
    sorted_stats   = sorted(stats, key=lambda x: x.get("total_messages", 0), reverse=True)
    top            = sorted_stats[0] if sorted_stats else {}

    # ── Métricas ──────────────────────────────────────────────────────────────
    st.markdown(
        f'<div class="m-grid">'
        f'<div class="m-card"><div class="m-icon">🎓</div>'
        f'<p class="m-val">{total_students}</p><p class="m-lbl">{L["students"]}</p></div>'
        f'<div class="m-card"><div class="m-icon">💬</div>'
        f'<p class="m-val">{total_msgs}</p><p class="m-lbl">{L["messages"]}</p></div>'
        f'<div class="m-card"><div class="m-icon">⚠️</div>'
        f'<p class="m-val">{total_fixes}</p><p class="m-lbl">{L["errors"]}</p></div>'
        f'<div class="m-card"><div class="m-icon">✅</div>'
        f'<p class="m-val">{total_fixes}</p><p class="m-lbl">{L["corrections"]}</p></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Insights da turma ─────────────────────────────────────────────────────
    with st.expander(L["insights"], expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(L["corr_rate"], f"{corr_rate:.0f}%")
        c2.metric(L["total_err"], total_fixes)
        c3.metric(L["err_types"], 0)
        c4.metric(L["msgs_std"],  total_msgs // total_students if total_students else 0)

    st.markdown("<hr class='db-divider'>", unsafe_allow_html=True)

    # Dica da seção via classe .section-tip (controlada no CSS externo)
    st.markdown(f"<p class='section-tip'>👥 {L['section_tip']}</p>", unsafe_allow_html=True)

    level_opts = ["Beginner", "Pre-Intermediate", "Intermediate", "Advanced", "Business English"]

    # ── Cards de alunos ───────────────────────────────────────────────────────
    for s in sorted_stats:
        name   = s.get("name", "") or s.get("username", "")
        uname  = s.get("username", "")
        level  = s.get("level", "—")
        focus  = s.get("focus", "—")
        msgs   = s.get("total_messages", 0)
        fixes  = s.get("corrections", 0)
        last   = s.get("last_activity", "")
        mpd    = round(msgs / 30, 1) if msgs > 0 else 0.0

        status_txt, _ = _student_status(msgs, last, lang)

        days = _days_inactive(last)
        if msgs == 0:            bcolor = "#c084fc"
        elif days and days > 10: bcolor = "#ff7a5c"
        elif days and days > 5:  bcolor = "#f0a500"
        else:                    bcolor = "#4ade80"

        user_profile        = (all_users.get(uname, {}).get("profile") or {})
        custom_prompt_saved = user_profile.get("custom_prompt", "")
        insight_key         = f"insight_{uname}"
        errors_key          = f"errors_{uname}"
        hits_key            = f"hits_{uname}"

        with st.expander(f"{name}  ·  {level}  ·  {status_txt}", expanded=False):

            # Borda lateral por status
            st.markdown(
                f'<style>details:has(summary span[title="{name}"]) '
                f'{{ border-left:3px solid {bcolor}; }}</style>',
                unsafe_allow_html=True,
            )

            # Métricas
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric(L["messages"],    msgs)
            mc2.metric(L["errors"],      fixes)
            mc3.metric(L["corrections"], fixes)
            mc4.metric("Msgs/dia",       mpd)

            # Meta via classe db-meta-txt
            st.markdown(
                f"<p class='db-meta-txt'>"
                f"<strong>{L['focus']}:</strong> {focus} &nbsp;|&nbsp; "
                f"<strong>{L['last_act']}:</strong> {last[:16] if last else '—'}"
                f"</p>",
                unsafe_allow_html=True,
            )
            st.markdown("<hr class='db-divider-soft'>", unsafe_allow_html=True)

            # Carrega erros/acertos uma vez por sessão
            if errors_key not in st.session_state:
                convs_list = list_conversations(uname)
                all_msgs   = []
                for cv in convs_list[:5]:
                    all_msgs.extend(load_conversation(uname, cv["id"], limit=30))
                errs, hits = _extract_errors_and_hits(all_msgs)
                st.session_state[errors_key] = errs
                st.session_state[hits_key]   = hits

            errs = st.session_state.get(errors_key, [])
            hits = st.session_state.get(hits_key, [])

            col_e, col_h = st.columns(2)
            with col_e:
                st.markdown(f"**⚠️ {L['errors_lbl']}**")
                if errs:
                    for err in errs:
                        st.markdown(
                            f'<span class="tag-err">{err["type"]}</span> '
                            f'<span style="font-size:.76rem;color:#8b949e;">{err["text"]}</span>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown(f"<span class='db-empty-hint'>{L['no_errs_s']}</span>", unsafe_allow_html=True)

            with col_h:
                st.markdown(f"**✅ {L['hits_lbl']}**")
                if hits:
                    for h in hits:
                        st.markdown(f'<span class="tag-hit">{h}</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f"<span class='db-empty-hint'>{L['no_hits']}</span>", unsafe_allow_html=True)

            st.markdown("<hr class='db-divider-soft'>", unsafe_allow_html=True)

            # ── AI Insight ────────────────────────────────────────────────────
            # Renderiza insight salvo (de sessões anteriores)
            if st.session_state.get(insight_key):
                st.markdown(
                    f'<div class="ins-box">'
                    f'<span class="ins-label">{L["ai_insight"]}</span>'
                    f'{st.session_state[insight_key]}</div>',
                    unsafe_allow_html=True,
                )

            # Placeholder para o insight recém-gerado aparecer aqui
            insight_placeholder = st.empty()

            # Botão de gerar — FORA de qualquer st.columns para garantir render
            if _btn("btn-action", L["gen_insight"], key=f"ins_{uname}"):
                with st.spinner(L["analyzing"]):
                    cl2, ml2 = list_conversations(uname), []
                    for cv in cl2[:3]:
                        ml2.extend(load_conversation(uname, cv["id"], limit=20))
                    texto, erro = _get_ai_insight(s, ml2, custom_prompt_saved)

                if erro:
                    st.error(f"Erro ao gerar insight: {erro}")
                elif texto:
                    st.session_state[insight_key] = texto
                    # Renderiza no placeholder logo acima do botão
                    insight_placeholder.markdown(
                        f'<div class="ins-box">'
                        f'<span class="ins-label">{L["ai_insight"]}</span>'
                        f'{texto}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.warning(L["no_conv"])

            st.markdown("<hr class='db-divider-soft'>", unsafe_allow_html=True)

            # Nível + Prompt
            col_lvl, _ = st.columns([2, 3])
            with col_lvl:
                cur_idx   = level_opts.index(level) if level in level_opts else 0
                new_level = _select(
                    "input-level", L["chg_level"], level_opts,
                    index=cur_idx, key=f"lvl_{uname}",
                )
                if new_level != level:
                    if _btn("btn-action", L["save"], key=f"slvl_{uname}"):
                        update_profile(uname, {"level": new_level})
                        st.success(L["level_saved"])
                        st.rerun()

            st.markdown(f"**{L['cust_prompt']}**")
            new_prompt = _textarea(
                "input-prompt", "p",
                value=custom_prompt_saved,
                placeholder=L["prompt_hint"],
                key=f"tp_{uname}", height=65,
                label_visibility="collapsed",
            )
            if _btn("btn-action", L["save"], key=f"sp_{uname}"):
                update_profile(uname, {"custom_prompt": new_prompt})
                st.session_state.pop(insight_key, None)
                st.success(L["prompt_saved"])
                st.rerun()

    st.markdown("<hr class='db-divider'>", unsafe_allow_html=True)

    # ── Gerenciamento ─────────────────────────────────────────────────────────
    with st.expander(L["manage"], expanded=False):
        options = [s["username"] for s in sorted_stats]
        labels  = [s.get("name", s["username"]) for s in sorted_stats]
        if options:
            sel_label = st.selectbox(L["select_std"], labels, key="mgmt_sel")
            sel_uname = options[labels.index(sel_label)] if sel_label in labels else None
            if sel_uname:
                col_a, col_b = st.columns([4, 1])
                with col_b:
                    if _btn("btn-danger", L["remove"], key="btn_rm", type="secondary"):
                        st.session_state["_confirm_rm"] = sel_uname
                if st.session_state.get("_confirm_rm") == sel_uname:
                    st.warning(L["confirm_rem"])
                    c1, c2 = st.columns(2)
                    with c1:
                        if _btn("btn-danger", L["confirm"], key="btn_cfm", type="primary"):
                            try:
                                from database import get_client
                                db = get_client()
                                for tbl in ("messages", "conversations", "sessions", "users"):
                                    db.table(tbl).delete().eq("username", sel_uname).execute()
                                st.session_state.pop("_confirm_rm", None)
                                st.success(f"{sel_label} {L['removed_ok']}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro: {e}")
                    with c2:
                        if _btn("btn-secondary", L["cancel"], key="btn_cncl"):
                            st.session_state.pop("_confirm_rm", None)
                            st.rerun()

    # ── Resumo ────────────────────────────────────────────────────────────────
    with st.expander(L["summary"], expanded=False):
        st.markdown(
            f"- **{L['messages']}/{L['students']}:** "
            f"{total_msgs // total_students if total_students else 0} {L['avg']}\n"
            f"- **{L['corr_rate']}:** {corr_rate:.1f}%\n"
            f"- **{L['most_active']}:** {top.get('name', 'N/A')} "
            f"({top.get('total_messages', 0)} msgs)"
        )