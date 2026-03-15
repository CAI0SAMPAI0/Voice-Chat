"""
guards/auth_helper.py — Autenticação persistente via cookie HMAC-SHA256.
Usa streamlit-cookies-controller que acessa o cookie do domínio correto.
"""

import streamlit as st
import base64
import hmac
import hashlib
import json
import os
from streamlit_cookies_controller import CookieController

_THIRTY_DAYS_MS = 60 * 60 * 24 * 30  # segundos

def _get_secret() -> bytes:
    try:
        return st.secrets["COOKIE_SECRET"].encode()
    except Exception:
        pass
    return os.getenv("COOKIE_SECRET", os.getenv("SUPABASE_KEY", "fallback")).encode()


class AuthHelper:
    COOKIE_NAME = "tati_voice_auth"

    def __init__(self):
        self.secret     = _get_secret()
        # IMPORTANTE: instanciar UMA vez no topo do app e reutilizar
        # Não instanciar dentro de funções chamadas múltiplas vezes
        self._ctrl = CookieController()

    def _sign(self, token: str) -> str:
        sig = hmac.new(self.secret, token.encode(), hashlib.sha256).digest()
        payload = {
            "token": base64.urlsafe_b64encode(token.encode()).decode(),
            "sig":   base64.urlsafe_b64encode(sig).decode(),
        }
        return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()

    def _verify(self, signed_value: str) -> str | None:
        try:
            data     = json.loads(base64.urlsafe_b64decode(signed_value).decode())
            token    = base64.urlsafe_b64decode(data["token"]).decode()
            expected = hmac.new(self.secret, token.encode(), hashlib.sha256).digest()
            received = base64.urlsafe_b64decode(data["sig"])
            if hmac.compare_digest(expected, received):
                return token
        except Exception:
            pass
        return None

    def save(self, token: str) -> None:
        """Salva o token assinado no cookie via CookieController."""
        signed = self._sign(token)
        self._ctrl.set(self.COOKIE_NAME, signed, max_age=_THIRTY_DAYS_MS)

    def get_token(self) -> str | None:
        """Lê e verifica o cookie. Retorna o token ou None."""
        raw = self._ctrl.get(self.COOKIE_NAME)
        if not raw:
            return None
        return self._verify(raw)

    def is_authenticated(self) -> bool:
        return self.get_token() is not None

    def clear(self) -> None:
        """Remove o cookie."""
        self._ctrl.remove(self.COOKIE_NAME)

    def login(self, token: str) -> None: self.save(token)
    def logout(self) -> None: self.clear()