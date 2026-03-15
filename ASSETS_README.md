# Teacher Tati — Estrutura de Assets

## Estrutura de pastas

```
teacher_tati/
├── app.py                        # Entry point (não muda)
├── database.py                   # Supabase (não muda)
├── ui_helpers.py                 # ← REFATORADO: carrega assets externos
├── tati_views/
│   ├── voice.py
│   ├── login.py
│   ├── history.py
│   ├── settings.py
│   └── dashboard.py
└── assets/
    ├── css/
    │   ├── global.css            # variáveis, reset Streamlit, animações base
    │   ├── sidebar.css           # layout sidebar fixa, toggle, botão seta
    │   ├── voice.css             # avatar, anel, bolhas, mic, controles de áudio
    │   ├── history.css           # cards de conversa, preview de mensagens
    │   └── dashboard.css        # métricas, tabela alunos, botões do login
    ├── js/
    │   ├── session.js            # localStorage, cookie, auto-login
    │   ├── sidebar.js            # toggle com persistência em sessionStorage
    │   ├── audio.js              # player TTS, volume, velocidade, botão global
    │   ├── avatar.js             # estados idle/listening/processing/speaking
    │   └── mic.js                # botão mic customizado → liga ao st.audio_input
    └── html/
        ├── avatar_card.html      # card do avatar (login + cabeçalho da voz)
        └── voice_screen.html     # tela de voz completa (iframe principal)
```

## Como usar os loaders em qualquer view

```python
from ui_helpers import load_css, load_js, load_html

# Injeta CSS de uma página específica
st.markdown(load_css("history.css"), unsafe_allow_html=True)

# Injeta CSS global (já chamado em inject_global_css())
st.markdown(load_css("global.css"), unsafe_allow_html=True)

# Renderiza um template HTML com variáveis
html = load_html("avatar_card.html",
    PROF_NAME   = "Teacher Tati",
    SUBTITLE    = "Voice English Coach",
    AVATAR_HTML = '<img class="av" src="...">',
    RING_COLOR  = "#f0a500",
    RING_COLOR_DIM  = "rgba(240,165,0,0.12)",
    RING_COLOR_GLOW = "rgba(240,165,0,0.25)",
)
st.markdown(html, unsafe_allow_html=True)
```

## Variáveis CSS disponíveis globalmente

Após `inject_global_css()` ser chamado, qualquer HTML inline pode usar:

```css
var(--bg-primary)       /* #060a10 */
var(--bg-secondary)     /* #0f1824 */
var(--bg-card)          /* #0d1420 */
var(--border-subtle)    /* #1a2535 */
var(--text-primary)     /* #e6edf3 */
var(--text-secondary)   /* #8b949e */
var(--text-muted)       /* #4a5a6a */
var(--accent)           /* #f0a500 */
var(--accent-dim)       /* rgba(240,165,0,0.15) */
var(--purple)           /* #8b5cf6 */
var(--success)          /* #2d6a4f */
var(--danger)           /* #e05c2a */
var(--radius-md)        /* 12px */
var(--transition)       /* all 0.2s ease */
```

## Como adicionar uma nova animação

Edite `assets/css/global.css` e adicione o `@keyframes`.
Use a classe em qualquer HTML inline:

```css
/* global.css */
@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}
.slide-up { animation: slideUp 0.3s ease forwards; }
```

```python
# Em qualquer view
st.markdown('<div class="slide-up">Conteúdo</div>', unsafe_allow_html=True)
```
