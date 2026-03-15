"""
guards/auth_helper.py — Cookie persistente com HMAC-SHA256.
Usa streamlit-cookies-controller (componente React — funciona no Cloud).
Instância única via get_auth() para evitar conflito de múltiplos componentes.
"""

import os
import base64
import hmac
import hashlib
import json
import streamlit as st
from streamlit_cookies_controller import CookieController

_THIRTY_DAYS = 60 * 60 * 24 * 30


def _get_secret() -> bytes:
    try:
        return st.secrets["COOKIE_SECRET"].encode()
    except Exception:
        pass
    env = os.getenv("COOKIE_SECRET", "")
    if env:
        return env.encode()
    try:
        return st.secrets["SUPABASE_KEY"].encode()
    except Exception:
        pass
    return os.getenv("SUPABASE_KEY", "fallback-troque").encode()


class AuthHelper:
    COOKIE_NAME = "tati_voice_auth"

    def __init__(self):
        self.secret = _get_secret()
        self._ctrl  = CookieController()

    # ── Assinatura ────────────────────────────────────────────────────────────

    def _sign(self, token: str) -> str:
        sig = hmac.new(self.secret, token.encode(), hashlib.sha256).digest()
        payload = {
            "token": base64.urlsafe_b64encode(token.encode()).decode(),
            "sig":   base64.urlsafe_b64encode(sig).decode(),
        }
        return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()

    def _verify(self, signed: str) -> str | None:
        try:
            data     = json.loads(base64.urlsafe_b64decode(signed).decode())
            token    = base64.urlsafe_b64decode(data["token"]).decode()
            expected = hmac.new(self.secret, token.encode(), hashlib.sha256).digest()
            received = base64.urlsafe_b64decode(data["sig"])
            if hmac.compare_digest(expected, received):
                return token
        except Exception:
            pass
        return None

    # ── API pública ───────────────────────────────────────────────────────────

    def save(self, token: str) -> None:
        self._ctrl.set(self.COOKIE_NAME, self._sign(token), max_age=_THIRTY_DAYS)

    def get_token(self) -> str | None:
        raw = self._ctrl.get(self.COOKIE_NAME)
        if not raw:
            return None
        return self._verify(raw)

    def is_authenticated(self) -> bool:
        return self.get_token() is not None

    def clear(self) -> None:
        self._ctrl.remove(self.COOKIE_NAME)

    # aliases
    def login(self, token: str) -> None: self.save(token)
    def logout(self) -> None: self.clear()


# ── Singleton — UMA instância por sessão ──────────────────────────────────────
# Usar get_auth() em vez de AuthHelper() diretamente.
# Múltiplas instâncias do CookieController conflitam entre si.

def get_auth() -> AuthHelper:
    if "_auth_instance" not in st.session_state:
        st.session_state["_auth_instance"] = AuthHelper()
    return st.session_state["_auth_instance"]