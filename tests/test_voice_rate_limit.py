"""
tests/test_voice_rate_limit.py
Sem mock de Streamlit — a função recebe o estado como parâmetro simples.
"""
import pytest
from tati_views.voice import _check_voice_rate_limit


def test_primeira_mensagem_permitida():
    state = {}
    allowed, msg = _check_voice_rate_limit("usuario_teste", state)
    assert allowed is True
    assert msg == ""


def test_limite_atingido_bloqueia():
    state = {}
    for _ in range(40):
        _check_voice_rate_limit("usuario_x", state)
    allowed, msg = _check_voice_rate_limit("usuario_x", state)
    assert allowed is False
    assert "Limite" in msg


def test_usuarios_diferentes_tem_contadores_separados():
    state = {}
    for _ in range(30):
        _check_voice_rate_limit("usuario_a", state)
    allowed, _ = _check_voice_rate_limit("usuario_b", state)
    assert allowed is True


def test_contador_reseta_apos_janela():
    import time
    state = {}
    # Simula bucket já expirado
    KEY = "_rl_voice_usuario_y"
    state[KEY] = {"count": 30, "reset_at": time.time() - 1}  # expirou 1s atrás
    allowed, msg = _check_voice_rate_limit("usuario_y", state)
    assert allowed is True  # janela resetou, deve permitir


def test_mensagem_de_erro_contem_minutos():
    state = {}
    for _ in range(40):          
        _check_voice_rate_limit("usuario_z", state)
    allowed, msg = _check_voice_rate_limit("usuario_z", state)
    assert "minuto" in msg.lower()