"""
pages/history.py — Tela de histórico de conversas.
Melhoria: cada mensagem do bot no histórico tem botão ▶ Ouvir
se o tts_b64 estiver salvo no banco.
"""

import json
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from database import (
    list_conversations,
    load_conversation,
    delete_conversation,
    new_conversation,
)
from ui_helpers import t, PROF_NAME
from guards.page_guard import page_guard, scroll_restore


@page_guard
def show_history() -> None:
    user     = st.session_state.user
    username = user["username"]
    profile  = user.get("profile", {})
    lang     = profile.get("language", "pt-BR")

    # Restaura scroll
    scroll_restore()

    st.markdown("""<style>
.hist-header{display:flex;align-items:center;gap:12px;padding:0 0 1.2rem;margin-bottom:1rem;border-bottom:1px solid #1a2535;}
.hist-header h2{margin:0;font-size:1.4rem;color:#e6edf3;font-weight:700;}
.hist-count{background:#1a2535;color:#8b949e;font-size:.7rem;padding:3px 10px;border-radius:20px;margin-left:auto;}
.hist-card{display:flex;align-items:center;background:#0d1420;border:1px solid #1a2535;border-radius:14px;margin-bottom:2px;overflow:hidden;transition:border-color .18s,box-shadow .18s;}
.hist-card:hover{border-color:#f0a50044;box-shadow:0 2px 16px rgba(240,165,0,.07);}
.hist-card-icon{flex-shrink:0;width:48px;display:flex;align-items:center;justify-content:center;font-size:1.1rem;color:#f0a500;padding:0 4px;align-self:stretch;border-right:1px solid #1a2535;background:#0a1020;}
.hist-card-body{flex:1;padding:12px 14px;min-width:0;}
.hist-card-title{font-size:.88rem;font-weight:600;color:#e6edf3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:5px;}
.hist-card-meta{display:flex;gap:12px;align-items:center;flex-wrap:wrap;}
.hist-meta-item{display:flex;align-items:center;gap:4px;font-size:.68rem;color:#4a5a6a;}
.hist-meta-dot{width:5px;height:5px;border-radius:50%;background:#1a2535;flex-shrink:0;}
.hist-open-row{margin-top:6px!important;margin-bottom:4px!important;padding-left:2px!important;}
.hist-open-row button,[.hist-open-row [data-testid="stButton"]>button{
    background:transparent!important;border:1px solid #1a2535!important;color:#3a6a8a!important;
    font-size:.75rem!important;padding:5px 12px!important;border-radius:8px!important;
    box-shadow:none!important;width:auto!important;min-height:30px!important;
    display:inline-flex!important;align-items:center!important;
}
.hist-open-row button:hover{color:#f0a500!important;background:rgba(240,165,0,.08)!important;border-color:rgba(240,165,0,.3)!important;}
.hist-del-row button,[data-testid="stButton"]>button.del{
    background:transparent!important;border:1px solid #1a2535!important;color:#3a4e5e!important;
    font-size:.85rem!important;padding:4px 8px!important;border-radius:8px!important;
    box-shadow:none!important;min-height:unset!important;height:32px!important;width:32px!important;
}
.hist-del-row button:hover{color:#e05c2a!important;border-color:rgba(224,92,42,.4)!important;background:rgba(224,92,42,.08)!important;}

/* ── Preview da conversa ── */
.conv-preview{padding:12px 16px;background:#070c15;border-radius:0 0 14px 14px;margin-bottom:8px;}
.preview-bubble{max-width:80%;padding:8px 12px;border-radius:14px;font-size:.8rem;line-height:1.5;margin-bottom:6px;}
.preview-bubble.user{align-self:flex-end;background:#2d6a4f;color:#fff;margin-left:auto;border-bottom-right-radius:4px;}
.preview-bubble.bot{align-self:flex-start;background:#1a1f2e;color:#e6edf3;border:1px solid #252d3d;border-bottom-left-radius:4px;}
.preview-label{font-size:.6rem;color:#4a5a6a;margin:2px 4px;}
.preview-label.right{text-align:right;}
.preview-play-btn{background:transparent;border:1px solid #1a2535;color:#3a6a8a;font-size:.7rem;padding:3px 10px;border-radius:6px;cursor:pointer;font-family:inherit;transition:all .15s;margin-bottom:6px;}
.preview-play-btn:hover{color:#f0a500;border-color:rgba(240,165,0,.4);}
.preview-play-btn.playing{color:#e05c2a;border-color:rgba(224,92,42,.5);}
</style>""", unsafe_allow_html=True)

    convs = list_conversations(username)

    st.markdown(f"""
<div class="pav-page">
<div class="hist-header">
    <h2>📄 {t('history', lang)}</h2>
    {"<span class='hist-count'>" + str(len(convs)) + " conversas</span>" if convs else ""}
</div>
</div>""", unsafe_allow_html=True)

    if not convs:
        st.markdown(
            f"<div style='padding:2rem;color:#4a5a6a;font-size:.9rem;'>"
            f"💬 {t('no_history', lang)}</div>",
            unsafe_allow_html=True)
        return

    for conv in convs:
        cid       = conv["id"]
        title     = conv.get("title") or conv.get("first_message", "") or f"Conversa {cid[:8]}"
        date_raw  = conv.get("updated_at", "") or conv.get("created_at", "") or conv.get("date", "")
        msg_count = conv.get("msg_count", 0)

        # Formata data
        date_fmt = date_raw[:16] if date_raw else "---"
        try:
            _d = datetime.fromisoformat(date_raw[:19])
            date_fmt = _d.strftime("%d/%m/%Y %H:%M")
        except Exception:
            pass

        col_open, col_del = st.columns([12, 1])

        with col_open:
            st.markdown(f"""
<div class="hist-card">
    <div class="hist-card-icon">🎙️</div>
    <div class="hist-card-body">
        <div class="hist-card-title">{title[:70]}{'…' if len(title)>70 else ''}</div>
        <div class="hist-card-meta">
            <div class="hist-meta-item">📅 {date_fmt}</div>
            <div class="hist-meta-dot"></div>
            <div class="hist-meta-item">💬 {msg_count} msg{'s' if msg_count != 1 else ''}</div>
        </div>
    </div>
</div>
<div class="hist-open-row">""", unsafe_allow_html=True)

            if st.button("▶ Abrir conversa", key=f"conv_{cid}", help=title):
                st.session_state.conv_id          = cid
                st.session_state["_vm_history"]   = []
                st.session_state["_vm_reply"]     = ""
                st.session_state["_vm_user_said"] = ""
                st.session_state.page             = "voice"
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

            # ── Preview das mensagens com botão ▶ por bolha ──
            if st.toggle("👁 Ver mensagens", key=f"preview_{cid}"):
                msgs = load_conversation(username, cid)
                if msgs:
                    _render_preview(msgs, cid)
                else:
                    st.markdown(
                        "<div style='color:#4a5a6a;font-size:.8rem;padding:8px 16px;'>Sem mensagens.</div>",
                        unsafe_allow_html=True)

        with col_del:
            st.markdown("<div class='hist-del-row' style='padding-top:8px;'>", unsafe_allow_html=True)
            if st.button("🗑", key=f"del_{cid}", help=t("del_conv", lang)):
                delete_conversation(username, cid)
                if st.session_state.conv_id == cid:
                    st.session_state.conv_id = None
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)


def _render_preview(msgs: list, conv_id: str) -> None:
    """
    Renderiza bolhas da conversa no histórico.
    Mensagens do bot com tts_b64 ganham botão ▶ Ouvir via JS.
    """
    # Serializa apenas o necessário para o JS
    bubbles_js = json.dumps([
        {
            "role":    m["role"],
            "content": (m.get("content") or "")[:300],   # limita para o preview
            "tts_b64": m.get("tts_b64", ""),
        }
        for m in msgs if m.get("content")
    ])
    prof_name_js = json.dumps(PROF_NAME)
    cid_js = json.dumps(conv_id)

    components.html(f"""<!DOCTYPE html><html><head>
<meta charset="UTF-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
html,body{{background:#070c15;font-family:'Sora',sans-serif;padding:12px 16px;}}
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600&display=swap');
.wrap{{display:flex;flex-direction:column;gap:6px;}}
.label{{font-size:.6rem;color:#4a5a6a;margin:4px 3px 1px;}}
.label.right{{text-align:right;}}
.bubble{{max-width:82%;padding:8px 12px;border-radius:14px;font-size:.8rem;line-height:1.5;word-break:break-word;}}
.bubble.user{{align-self:flex-end;background:#2d6a4f;color:#fff;border-bottom-right-radius:4px;margin-left:auto;}}
.bubble.bot{{align-self:flex-start;background:#1a1f2e;color:#e6edf3;border:1px solid #252d3d;border-bottom-left-radius:4px;}}
.play-btn{{
    align-self:flex-start;
    background:transparent;border:1px solid #1a2535;color:#3a6a8a;
    font-size:.7rem;padding:3px 10px;border-radius:6px;cursor:pointer;
    font-family:inherit;transition:all .15s;margin-bottom:2px;
}}
.play-btn:hover{{color:#f0a500;border-color:rgba(240,165,0,.4);background:rgba(240,165,0,.06);}}
.play-btn.playing{{color:#e05c2a;border-color:rgba(224,92,42,.5);}}
</style></head><body>
<div class="wrap" id="wrap"></div>
<script>
(function(){{
var BUBBLES   = {bubbles_js};
var PROF_NAME = {prof_name_js};
var wrap = document.getElementById('wrap');
var currentAudio = null;

function playAudio(b64, btn){{
    if(currentAudio && !currentAudio.paused){{
        currentAudio.pause(); currentAudio=null;
        document.querySelectorAll('.play-btn').forEach(function(b){{b.textContent='▶ Ouvir';b.classList.remove('playing');}});
    }}
    if(!b64) return;
    var audio = new Audio('data:audio/mp3;base64,'+b64);
    audio.volume = 1.0;
    currentAudio = audio;
    btn.textContent='⏹ Parar'; btn.classList.add('playing');
    audio.onended = function(){{ btn.textContent='▶ Ouvir'; btn.classList.remove('playing'); currentAudio=null; }};
    audio.onerror = function(){{ btn.textContent='▶ Ouvir'; btn.classList.remove('playing'); currentAudio=null; }};
    audio.play().catch(function(){{}});
}}

BUBBLES.forEach(function(msg){{
    var role = msg.role==='user' ? 'user' : 'bot';
    var lbl  = document.createElement('div');
    lbl.className = 'label' + (role==='user' ? ' right' : '');
    lbl.textContent = role==='user' ? 'Você' : PROF_NAME;

    var bub = document.createElement('div');
    bub.className = 'bubble '+role;
    bub.textContent = msg.content + (msg.content.length===300 ? '…' : '');

    wrap.appendChild(lbl);
    wrap.appendChild(bub);

    if(role==='bot' && msg.tts_b64){{
        var btn = document.createElement('button');
        btn.className='play-btn';
        btn.textContent='▶ Ouvir';
        btn.addEventListener('click', function(){{
            var isPlaying = currentAudio && !currentAudio.paused;
            if(isPlaying && btn.classList.contains('playing')){{
                currentAudio.pause(); currentAudio=null;
                btn.textContent='▶ Ouvir'; btn.classList.remove('playing');
            }}else{{
                playAudio(msg.tts_b64, btn);
            }}
        }});
        wrap.appendChild(btn);
    }}
}});
}})();
</script>
</body></html>""", height=min(400, len(msgs) * 70 + 40), scrolling=True)
