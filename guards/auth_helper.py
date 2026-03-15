import streamlit as st
import base64
import hmac
import hashlib
import json
import streamlit.components.v1 as components

_THIRTY_DAYS = 60 * 60 * 24 * 30   # segundos


class AuthHelper:
    COOKIE_NAME = "tati_voice_auth"

    def __init__(self):
        # COOKIE_SECRET deve estar em .streamlit/secrets.toml
        self.secret = st.secrets["COOKIE_SECRET"].encode()

    # ── Assinatura ────────────────────────────────────────────────────────────

    def _sign(self, token: str) -> str:
        """Assina o token e retorna um valor base64 seguro para o cookie."""
        signature = hmac.new(
            self.secret,
            token.encode(),
            hashlib.sha256,
        ).digest()

        payload = {
            "token": base64.urlsafe_b64encode(token.encode()).decode(),
            "sig":   base64.urlsafe_b64encode(signature).decode(),
        }

        return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()

    def _verify(self, signed_value: str) -> str | None:
        """Verifica a assinatura e retorna o token original, ou None se inválido."""
        try:
            data  = json.loads(base64.urlsafe_b64decode(signed_value).decode())
            token = base64.urlsafe_b64decode(data["token"]).decode()

            expected = hmac.new(
                self.secret,
                token.encode(),
                hashlib.sha256,
            ).digest()

            received = base64.urlsafe_b64decode(data["sig"])

            if hmac.compare_digest(expected, received):
                return token
        except Exception:
            pass
        return None

    # ── API pública ───────────────────────────────────────────────────────────

    def save(self, token: str) -> None:
        """Salva o token assinado no cookie (30 dias)."""
        signed = self._sign(token)
        components.html(
            f"""<!DOCTYPE html><html><head>
            <style>html,body{{margin:0;padding:0;overflow:hidden;}}</style>
            </head><body><script>
            document.cookie = [
                "{self.COOKIE_NAME}={signed}",
                "path=/",
                "max-age={_THIRTY_DAYS}",
                "SameSite=Strict"
            ].join("; ");
            </script></body></html>""",
            height=0,
        )

    def get_token(self) -> str | None:
        """Lê e verifica o cookie. Retorna o token ou None."""
        raw = st.context.cookies.get(self.COOKIE_NAME)
        if not raw:
            return None
        return self._verify(raw)

    def is_authenticated(self) -> bool:
        return self.get_token() is not None

    def clear(self) -> None:
        """Remove o cookie (logout)."""
        components.html(
            f"""<!DOCTYPE html><html><head>
            <style>html,body{{margin:0;padding:0;overflow:hidden;}}</style>
            </head><body><script>
            document.cookie = "{self.COOKIE_NAME}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            </script></body></html>""",
            height=0,
        )

    # Alias para manter compatibilidade com o nome original
    def login(self, token: str) -> None:
        self.save(token)

    def logout(self) -> None:
        self.clear()
