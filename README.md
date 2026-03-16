# Teacher Tati — Voice App

App de conversação em inglês por voz. Versão focada em Modo Conversa.

## Estrutura

```
chatbot_tati_voice/
├── app.py                  # App principal
├── requirements.txt
├── .streamlit/
│   └── config.toml         # Tema dark customizado
└── README.md

# Arquivos compartilhados do projeto original (colocar na mesma pasta):
├── database.py
├── transcriber.py
├── tts.py
├── assets/
│   ├── tati.png            # Foto da professora
│   ├── avatar_base.png     # (opcional) frames para animação de boca
│   ├── avatar_closed.png
│   ├── avatar_mid.png
│   └── avatar_open.png
```

## Deploy no Streamlit Cloud

1. Faça upload desta pasta como repositório Git
2. No Streamlit Cloud, selecione `app.py` como entry point
3. Em **Secrets**, adicione:
   ```
   ANTHROPIC_API_KEY = "sk-ant-..."
   PROFESSOR_NAME = "Teacher Tati"
   PROFESSOR_PHOTO = "assets/tati.png"
   ```

## Diferenças do app original

| Feature            | app original | app_voice |
|--------------------|:---:|:---:|
| Chat de texto      | ✅  | ❌  |
| Modo Conversa (voz)| ✅  | ✅  |
| Histórico          | ✅  | ✅  |
| Configurações      | ✅  | ✅  |
| Dashboard professor| ✅  | ✅  |
| Anexar arquivos    | ✅  | ❌  |
| Gerar PDF/DOCX     | ✅  | ❌  |

## Contas padrão

- **Programador** (aluno Advanced) — criado via tela de registro
- **Professor** — role `professor`, criado direto no banco ou via `database.py`

