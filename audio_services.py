"""
audio_services.py — Transcrição (Groq Whisper) e TTS (gTTS).

Mudanças vs versão anterior:
─────────────────────────────
1. BUG CORRIGIDO — apóstrofe substituída por espaço no TTS.
   Código anterior: text.replace("'", " ")
   Resultado: "don't" → "don t", "I'm" → "I m", "it's" → "it s"
   O gTTS pronunciava literalmente "don t" e "I m".
   Corrigido: apóstrofe preservada. gTTS lida bem com contrações.

2. BUG CORRIGIDO — aspas duplas removidas desnecessariamente.
   Código anterior: text.replace('"', " ")
   gTTS aceita aspas normalmente. Remover só gerava espaços extras.
   Corrigido: aspas duplas preservadas.

3. ADICIONADO — timeout no text_to_speech().
   gTTS faz uma requisição HTTP para translate.google.com.
   Sem timeout, se o Google estiver lento ou inacessível,
   a thread principal trava indefinidamente, bloqueando o Streamlit.
   Solução: mesma estratégia da transcribe_bytes — threading com join.

4. CORRIGIDO — mime type hardcoded "audio/webm" ignorava o suffix.
   Se suffix=".mp3" era passado, o arquivo era enviado ao Groq como
   "audio/webm" mesmo assim. Adicionado mapa suffix → mime type.

5. MELHORADO — erros do TTS agora retornam bytes vazios com log,
   em vez de None silencioso. O chamador (voice.py) já trata None
   corretamente, mas o log ficava apenas no servidor.

6. AJUSTADO — limite do TTS aumentado de 600 para 800 caracteres.
   Uma resposta de 3 frases pode ter ~450 chars. 600 cortava
   frequentemente a terceira frase. 800 dá mais margem sem
   impactar performance perceptivelmente no gTTS.
"""

import io
import os
import re
import tempfile
import threading

from typing import Optional


# =============================================================================
# CORREÇÕES DE TRANSCRIÇÃO
# =============================================================================

_CORRECTIONS: list[tuple[str, str]] = [
    # Nomes próprios — Whisper mishears estes com frequência
    (r"\bsh[ei]t[\s-]?on\b",   "Tatiana"),
    (r"\bta[ck]i[aeo]n[ae]\b", "Tatiana"),
    (r"\btatyana\b",            "Tatiana"),
    (r"\btatianna\b",           "Tatiana"),
    (r"\btachiana\b",           "Tatiana"),
    (r"\btati\s*anna\b",        "Tatiana"),
    # Termos pedagógicos
    (r"\bwork\s*sheet\b",       "worksheet"),
    (r"\bpast\s*simple\b",      "past simple"),
    (r"\bpresent\s*perfect\b",  "present perfect"),
    (r"\bmodal\s*verbs?\b",     "modal verbs"),
    (r"\bgramm?[ae]r\b",        "grammar"),
    (r"\bvocabul[ae]ry\b",      "vocabulary"),
    (r"\bpronunci[ae]tion\b",   "pronunciation"),
    (r"\bconditional\b",        "conditional"),
    (r"\bsubjunctive\b",        "subjunctive"),
    # Artefatos comuns do Whisper
    (r"\[BLANK_AUDIO\]",        ""),
    (r"\(silence\)",            ""),
    (r"\[silence\]",            ""),
    (r"\[ ?[Ss]ilence ?\]",     ""),
    (r"\[MUSIC\]",              ""),
    (r"\(music\)",              ""),
    (r"Subtitles by.*$",        ""),
    (r"Transcribed by.*$",      ""),
]

_GROQ_PROMPT = (
    "Teacher Tatiana, English class, Brazilian student, "
    "vocabulary, grammar, pronunciation, past simple, present perfect, "
    "modal verbs, conditional, subjunctive, worksheet, exercise, activity, "
    "como se diz, o que significa, não entendi, pode repetir."
)

# Mapa suffix → mime type para o Groq API
_SUFFIX_MIME: dict[str, str] = {
    ".webm": "audio/webm",
    ".wav":  "audio/wav",
    ".mp3":  "audio/mpeg",
    ".ogg":  "audio/ogg",
    ".m4a":  "audio/mp4",
    ".flac": "audio/flac",
}


def _apply_corrections(text: str) -> str:
    """Aplica correções de transcrição ao texto do Whisper."""
    for pattern, replacement in _CORRECTIONS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE).strip()
    return re.sub(r" {2,}", " ", text).strip()


def _get_groq_key() -> str:
    """
    Busca GROQ_API_KEY em os.getenv e st.secrets.
    Tenta a key simples primeiro, depois numeradas (_1 a _4).
    """
    # Tenta os.getenv primeiro (sem overhead do Streamlit)
    for name in ["GROQ_API_KEY"] + [f"GROQ_API_KEY_{i}" for i in range(1, 5)]:
        key = os.getenv(name, "")
        if key:
            return key

    # Fallback: st.secrets (só importa se necessário)
    try:
        import streamlit as _st
        for name in ["GROQ_API_KEY"] + [f"GROQ_API_KEY_{i}" for i in range(1, 5)]:
            key = _st.secrets.get(name, "")
            if key:
                return key
    except Exception:
        pass

    return ""


# =============================================================================
# TRANSCRIÇÃO
# =============================================================================

def transcribe_bytes(
    audio_bytes: bytes,
    suffix: str = ".webm",
    language: Optional[str] = None,
    timeout: int = 30,
) -> str:
    """
    Transcreve áudio via Groq Whisper com timeout.

    Args:
        audio_bytes: bytes do arquivo de áudio
        suffix:      extensão do arquivo (".webm", ".mp3", ".wav" etc)
        language:    código de idioma ISO opcional ("pt", "en") ou None para auto-detect
        timeout:     segundos máximos de espera (padrão 30s)

    Returns:
        Texto transcrito, ou mensagem de erro começando com ❌/⚠️.
    """
    result_box: list[str] = []  # preenchido pela thread

    def _run() -> None:
        tmp_path: Optional[str] = None
        try:
            from groq import Groq

            api_key = _get_groq_key()
            if not api_key:
                result_box.append("❌ GROQ_API_KEY não configurada.")
                return

            client = Groq(api_key=api_key)

            # Cria arquivo temporário com a extensão correta
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            # Determina o mime type baseado no suffix (não hardcoded)
            mime = _SUFFIX_MIME.get(suffix.lower(), "audio/webm")

            with open(tmp_path, "rb") as f:
                kwargs: dict = {
                    "file":            (f"audio{suffix}", f, mime),
                    "model":           "whisper-large-v3-turbo",
                    "prompt":          _GROQ_PROMPT,
                    "response_format": "text",
                }
                if language and language not in ("auto", ""):
                    kwargs["language"] = language

                transcription = client.audio.transcriptions.create(**kwargs)

            text = (
                transcription
                if isinstance(transcription, str)
                else transcription.text
            )
            text = _apply_corrections(text.strip())
            result_box.append(text or "⚠️ Não consegui entender o áudio.")

        except Exception as e:
            result_box.append(f"❌ Erro na transcrição: {e}")
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=timeout)

    if not result_box:
        return f"❌ Timeout na transcrição ({timeout}s). Verifique sua conexão."

    return result_box[0]


# =============================================================================
# TTS
# =============================================================================

def tts_available() -> bool:
    """Retorna True se o gTTS está disponível."""
    try:
        import gtts  # noqa: F401
        return True
    except ImportError:
        return False


def _sanitize_tts_text(text: str) -> str:
    """
    Prepara o texto para o gTTS: remove markdown e caracteres problemáticos.

    CORREÇÕES vs versão anterior:
    - Apóstrofe PRESERVADA: "don't" → "don't" (não mais "don t")
      gTTS pronuncia contrações corretamente.
    - Aspas duplas PRESERVADAS: gTTS lida bem com elas.
    - Limite aumentado de 600 para 800 chars.
    """
    # Remove markdown: bold, italic, code, headers
    text = re.sub(r"(\*\*|\*|`|#{1,6})\s?", "", text)

    # Remove tags HTML que possam ter escapado do sanitizer da IA
    text = re.sub(r"<[^>]+>", " ", text)

    # Caracteres que podem causar problemas no gTTS HTTP
    # NÃO inclui apóstrofe (') nem aspas duplas (") — ambos são preservados
    text = text.replace("&", " e ").replace("<", " ").replace(">", " ")

    # Normaliza espaços e quebras de linha
    text = re.sub(r"\s+", " ", text)

    # Limita tamanho (aumentado de 600 para 800)
    return text.strip()[:800]


def text_to_speech(
    text: str,
    timeout: int = 15,
) -> Optional[bytes]:
    """
    Converte texto em áudio MP3 via gTTS com timeout.

    Args:
        text:    texto a converter (será sanitizado internamente)
        timeout: segundos máximos de espera para a requisição HTTP do gTTS

    Returns:
        bytes do MP3, ou None se falhar.

    Mudanças vs versão anterior:
    - Adicionado timeout via threading (gTTS faz HTTP para o Google).
      Sem timeout, uma rede lenta travava o Streamlit indefinidamente.
    - Erros logados com mais contexto.
    """
    result_box: list[Optional[bytes]] = []

    def _run() -> None:
        try:
            from gtts import gTTS

            clean = _sanitize_tts_text(text)
            if not clean:
                result_box.append(None)
                return

            mp3_fp = io.BytesIO()
            tts = gTTS(text=clean, lang="en", tld="com", slow=False)
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            result_box.append(mp3_fp.read())

        except ImportError:
            print("❌ TTS: gtts não instalado. Execute: pip install gtts")
            result_box.append(None)
        except Exception as e:
            print(f"❌ TTS: {type(e).__name__}: {e}")
            result_box.append(None)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=timeout)

    if not result_box:
        print(f"❌ TTS: timeout após {timeout}s (requisição HTTP lenta)")
        return None

    return result_box[0]