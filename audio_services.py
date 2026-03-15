import io
import os
import re
import tempfile

from typing import Optional


# =============================================================================
# TRANSCRIPTION
# =============================================================================

_CORRECTIONS: list[tuple[str, str]] = [
    (r"\bsh[ei]t[\s-]?on\b",    "Tatiana"),
    (r"\bta[ck]i[aeo]n[ae]\b",  "Tatiana"),
    (r"\btatyana\b",             "Tatiana"),
    (r"\btatianna\b",            "Tatiana"),
    (r"\btachiana\b",            "Tatiana"),
    (r"\btati\s*anna\b",         "Tatiana"),
    (r"\bwork\s*sheet\b",        "worksheet"),
    (r"\bpast\s*simple\b",       "past simple"),
    (r"\bpresent\s*perfect\b",   "present perfect"),
    (r"\bmodal\s*verbs?\b",      "modal verbs"),
    (r"\bgramm?[ae]r\b",         "grammar"),
    (r"\bvocabul[ae]ry\b",       "vocabulary"),
    (r"\bpronunci[ae]tion\b",    "pronunciation"),
    (r"\bconditional\b",         "conditional"),
    (r"\bsubjunctive\b",         "subjunctive"),
    (r"\[BLANK_AUDIO\]",         ""),
    (r"\(silence\)",             ""),
    (r"\[silence\]",             ""),
    (r"\[ ?[Ss]ilence ?\]",      ""),
    (r"\[MUSIC\]",               ""),
    (r"\(music\)",               ""),
    (r"Subtitles by.*$",         ""),
    (r"Transcribed by.*$",       ""),
]

_GROQ_PROMPT = (
    "Teacher Tatiana, English class, Brazilian student, "
    "vocabulary, grammar, pronunciation, past simple, present perfect, "
    "modal verbs, conditional, subjunctive, worksheet, exercise, activity, "
    "como se diz, o que significa, não entendi, pode repetir."
)


def _apply_corrections(text: str) -> str:
    for pattern, replacement in _CORRECTIONS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE).strip()
    return re.sub(r" {2,}", " ", text).strip()


def transcribe_bytes(
    audio_bytes: bytes,
    suffix: str = ".wav",
    language: Optional[str] = None,
) -> str:
    tmp_path: Optional[str] = None
    try:
        from groq import Groq

        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            return "❌ GROQ_API_KEY não configurada."

        client = Groq(api_key=api_key)

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            kwargs = {
                "file": (f"audio{suffix}", f, "audio/webm"),
                "model": "whisper-large-v3-turbo",
                "prompt": _GROQ_PROMPT,
                "response_format": "text",
            }
            if language and language not in ("auto", ""):
                kwargs["language"] = language

            transcription = client.audio.transcriptions.create(**kwargs)

        text = transcription if isinstance(transcription, str) else transcription.text
        text = _apply_corrections(text.strip())

        return text or "⚠️ Não consegui entender o áudio. Tente novamente."

    except Exception as e:
        return f"❌ Erro na transcrição: {e}"

    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


# =============================================================================
# TTS
# =============================================================================


def tts_available() -> bool:
    return True


def _sanitize_tts_text(text: str) -> str:
    """
    Remove caracteres problemáticos e markdown antes de mandar para o gTTS.
    Limita em 600 caracteres e normaliza espaços.
    """
    # Remove markdown básico
    text = re.sub(r"(\*\*|\*|`|_|#)", "", text)
    # Remove caracteres especiais que podem quebrar o TTS
    text = text.replace("<", " ").replace(">", " ")
    text = text.replace("&", " ").replace('"', " ").replace("'", " ")
    # Normaliza espaços múltiplos
    text = re.sub(r"\s+", " ", text)
    # Limita tamanho
    return text.strip()[:600]


def text_to_speech(text: str) -> Optional[bytes]:
    try:
        from gtts import gTTS

        clean = _sanitize_tts_text(text)
        if not clean:
            return None

        mp3_fp = io.BytesIO()
        tts = gTTS(text=clean, lang="en", tld="com", slow=False)
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return mp3_fp.read()
    except Exception as e:
        print(f"❌ TTS: {e}")
        return None

