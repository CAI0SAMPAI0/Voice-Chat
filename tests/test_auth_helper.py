"""tests/test_auth_helper.py"""
import pytest
from unittest.mock import MagicMock, patch
import streamlit as st


# Precisamos mockar st.secrets antes de importar auth_helper
@pytest.fixture(autouse=True)
def mock_streamlit(monkeypatch):
    monkeypatch.setattr("streamlit.secrets", {}, raising=False)


def _make_auth():
    """Cria AuthHelper com segredo fixo para testes."""
    with patch("guards.auth_helper.CookieController"):
        from guards.auth_helper import AuthHelper
        auth = AuthHelper.__new__(AuthHelper)
        auth.secret = b"segredo_de_teste_fixo_32bytes___"
        auth._ctrl  = MagicMock()
        return auth


def test_sign_e_verify_roundtrip():
    auth  = _make_auth()
    token = "token_de_sessao_qualquer"
    signed = auth._sign(token)
    assert auth._verify(signed) == token

def test_verify_rejeita_token_adulterado():
    auth   = _make_auth()
    signed = auth._sign("token_original")
    # Adultera o payload
    adulterado = signed[:-4] + "XXXX"
    assert auth._verify(adulterado) is None

def test_verify_rejeita_string_invalida():
    auth = _make_auth()
    assert auth._verify("isso_nao_e_valido") is None
    assert auth._verify("") is None

def test_sign_tokens_diferentes_geram_assinaturas_diferentes():
    auth = _make_auth()
    s1 = auth._sign("token_a")
    s2 = auth._sign("token_b")
    assert s1 != s2