"""
Rodar com: pytest tests/
"""
import pytest
from unittest.mock import MagicMock, patch
from database import (
    hash_password,
    _verify_password,
    _needs_migration,
    _sha256_hex,
)


# ── Testes de hash ────────────────────────────────────────────────────────────

def test_hash_password_retorna_bcrypt():
    h = hash_password("minhasenha123")
    assert h.startswith("$2b$")

def test_hash_password_rounds_12():
    h = hash_password("minhasenha123")
    assert h.startswith("$2b$12$")

def test_hash_password_diferente_a_cada_chamada():
    # bcrypt usa salt aleatório — dois hashes da mesma senha são diferentes
    h1 = hash_password("mesmasenha")
    h2 = hash_password("mesmasenha")
    assert h1 != h2


# ── Testes de verificação ─────────────────────────────────────────────────────

def test_verify_password_bcrypt_correto():
    h = hash_password("senha_correta")
    assert _verify_password("senha_correta", h) is True

def test_verify_password_bcrypt_incorreto():
    h = hash_password("senha_correta")
    assert _verify_password("senha_errada", h) is False

def test_verify_password_sha256_legado_correto():
    plain = "senha_antiga"
    stored = _sha256_hex(plain)
    assert _verify_password(plain, stored) is True

def test_verify_password_sha256_legado_incorreto():
    stored = _sha256_hex("senha_certa")
    assert _verify_password("senha_errada", stored) is False

def test_verify_password_string_vazia():
    h = hash_password("qualquer")
    assert _verify_password("", h) is False
    assert _verify_password("qualquer", "") is False

def test_verify_password_hash_invalido():
    assert _verify_password("senha", "isso_nao_e_hash") is False


# ── Testes de migração ────────────────────────────────────────────────────────

def test_needs_migration_sha256_retorna_true():
    stored = _sha256_hex("qualquer_senha")
    assert _needs_migration(stored) is True

def test_needs_migration_bcrypt_retorna_false():
    stored = hash_password("qualquer_senha")
    assert _needs_migration(stored) is False

def test_needs_migration_string_invalida():
    assert _needs_migration("curta") is False
    assert _needs_migration("") is False