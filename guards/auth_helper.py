"""
guards/auth_helper.py — Autenticação persistente via cookie HMAC-SHA256.
COOKIE_SECRET é opcional — se não existir, usa o SUPABASE_KEY como fallback.
"""

import os
import streamlit as st
import base64
import hmac
import hashlib
import json
import streamlit.components.v1 as components

_THIRTY_DAYS = 60 * 60 * 24 * 30


def _get_secret() -> bytes:
    """Lê COOKIE_SECRET de secrets ou env, com fallback seguro."""
    try:
        return st.secrets["COOKIE_SECRET"].encode()
    except Exception:
        pass
    env = os.getenv("COOKIE_SECRET", "")
    if env:
        return env.encode()
    # Fallback: usa SUPABASE_KEY que já existe no projeto
    try:
        return st.secrets["SUPABASE_KEY"].encode()
    except Exception:
        pass
    return os.getenv("SUPABASE_KEY", "fallback-troque-isto").encode()


class AuthHelper:
    COOKIE_NAME = "tati_voice_auth"

    def __init__(self):
        self.secret = _get_secret()

    def _sign(self, token: str) -> str:
        signature = hmac.new(self.secret, token.encode(), hashlib.sha256).digest()
        payload = {
            "token": base64.urlsafe_b64encode(token.encode()).decode(),
            "sig":   base64.urlsafe_b64encode(signature).decode(),
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
        signed = self._sign(token)
        components.html(f"""<!DOCTYPE html><html><head>
<style>html,body{{margin:0;padding:0;overflow:hidden;}}</style>
</head><body><script>
document.cookie = "{self.COOKIE_NAME}={signed}; path=/; max-age={_THIRTY_DAYS}; SameSite=Strict";
</script></body></html>""", height=0)

    def get_token(self) -> str | None:
        raw = st.context.cookies.get(self.COOKIE_NAME)
        if not raw:
            return None
        return self._verify(raw)

    def is_authenticated(self) -> bool:
        return self.get_token() is not None

    def clear(self) -> None:
        components.html(f"""<!DOCTYPE html><html><head>
<style>html,body{{margin:0;padding:0;overflow:hidden;}}</style>
</head><body><script>
document.cookie = "{self.COOKIE_NAME}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
</script></body></html>""", height=0)

    def login(self, token: str) -> None: self.save(token)
    def logout(self) -> None: self.clear()
