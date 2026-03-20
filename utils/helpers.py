import base64
import os
from pathlib import Path

import streamlit as st

PHOTO_PATH = os.getenv("PROFESSOR_PHOTO", "assets/tati.png")
PROF_NAME  = os.getenv("PROFESSOR_NAME",  "Teacher Tati")


# ── Imagens da professora ─────────────────────────────────────────────────────

def get_photo_b64() -> str | None:
    """Lê a foto da professora e devolve como data-URI base64."""
    p = Path(PHOTO_PATH)
    if p.exists():
        ext  = p.suffix.lower().replace(".", "")
        mime = "jpeg" if ext in ("jpg", "jpeg") else ext
        return f"data:image/{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"
    return None


@st.cache_data(show_spinner=False)
def get_tati_mini_b64() -> str:
    """Lê a foto da Tati uma única vez e reutiliza em todo o app."""
    for _p in [
        Path("assets/tati.png"), Path("assets/tati.jpg"),
        Path(__file__).parent.parent / "assets" / "tati.png",
        Path(__file__).parent.parent / "assets" / "tati.jpg",
    ]:
        if _p.exists():
            _ext  = _p.suffix.lstrip(".").lower()
            _mime = "jpeg" if _ext in ("jpg", "jpeg") else _ext
            return f"data:image/{_mime};base64,{base64.b64encode(_p.read_bytes()).decode()}"
    return get_photo_b64() or ""