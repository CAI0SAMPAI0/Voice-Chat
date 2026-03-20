import os
import random
from typing import Literal
import streamlit as st


class APIKeyManager:
    """Gerencia múltiplas keys de diferentes providers, alternando entre elas."""
    
    def __init__(self):
        # Carrega keys do .env / secrets
        self.claude_keys = [
            os.getenv(f"ANTHROPIC_API_KEY_{i}", "") or st.secrets.get(f"ANTHROPIC_API_KEY_{i}", "")
            for i in range(1, 5)
        ]
        self.claude_keys = [k for k in self.claude_keys if k]  # Remove vazias
        
        self.gemini_keys = [
            os.getenv(f"GEMINI_API_KEY_{i}", "") or st.secrets.get(f"GEMINI_API_KEY_{i}", "")
            for i in range(1, 5)
        ]
        self.gemini_keys = [k for k in self.gemini_keys if k]  # Remove vazias
        
        # Índices para rotação (incrementam a cada chamada)
        self.claude_index = 0
        self.gemini_index = 0
        
        # Log para debug
        self._log_status()
    
    def _log_status(self):
        """Loga quantas keys foram encontradas (apenas uma vez)."""
        if "_key_manager_logged" not in st.session_state:
            print(f"[KeyManager] Claude keys carregadas: {len(self.claude_keys)}")
            print(f"[KeyManager] Gemini keys carregadas: {len(self.gemini_keys)}")
            st.session_state["_key_manager_logged"] = True
    
    def get_claude_key(self) -> str:
        """
        Retorna uma key Claude (rotaciona sequencialmente entre as 4).
        
        Raises:
            ValueError: Se nenhuma key Claude foi configurada
        """
        if not self.claude_keys:
            raise ValueError(
                "❌ Nenhuma ANTHROPIC_API_KEY encontrada no .env ou Secrets.\n"
                "Configure: ANTHROPIC_API_KEY_1, ANTHROPIC_API_KEY_2, etc."
            )
        
        key = self.claude_keys[self.claude_index]
        self.claude_index = (self.claude_index + 1) % len(self.claude_keys)
        return key
    
    def get_gemini_key(self) -> str:
        """
        Retorna uma key Gemini (rotaciona sequencialmente entre as 4).
        
        Raises:
            ValueError: Se nenhuma key Gemini foi configurada
        """
        if not self.gemini_keys:
            raise ValueError(
                "❌ Nenhuma GEMINI_API_KEY encontrada no .env ou Secrets.\n"
                "Configure: GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc."
            )
        
        key = self.gemini_keys[self.gemini_index]
        self.gemini_index = (self.gemini_index + 1) % len(self.gemini_keys)
        return key
    
    def get_random_claude_key(self) -> str:
        """Retorna uma key Claude aleatória (sem rotação previsível)."""
        if not self.claude_keys:
            raise ValueError("❌ Nenhuma ANTHROPIC_API_KEY configurada")
        return random.choice(self.claude_keys)
    
    def get_random_gemini_key(self) -> str:
        """Retorna uma key Gemini aleatória (sem rotação previsível)."""
        if not self.gemini_keys:
            raise ValueError("❌ Nenhuma GEMINI_API_KEY configurada")
        return random.choice(self.gemini_keys)
    
    def get_key(self, provider: Literal["claude", "gemini"], random_mode: bool = False) -> str:
        """
        Retorna uma key do provider especificado.
        
        Args:
            provider: "claude" ou "gemini"
            random_mode: Se True, alterna aleatoriamente. Se False, rotaciona.
        
        Returns:
            String da API key
        
        Raises:
            ValueError: Se provider é inválido ou nenhuma key foi encontrada
        """
        if provider == "claude":
            return self.get_random_claude_key() if random_mode else self.get_claude_key()
        elif provider == "gemini":
            return self.get_random_gemini_key() if random_mode else self.get_gemini_key()
        else:
            raise ValueError(f"Provider desconhecido: {provider}. Use 'claude' ou 'gemini'")
    
    def status(self) -> dict:
        """Retorna o status atual do gerenciador."""
        return {
            "claude_keys_loaded": len(self.claude_keys),
            "gemini_keys_loaded": len(self.gemini_keys),
            "claude_index": self.claude_index,
            "gemini_index": self.gemini_index,
            "claude_ready": len(self.claude_keys) > 0,
            "gemini_ready": len(self.gemini_keys) > 0,
        }


# ── Instância global (singleton) ─────────────────────────────────────────

@st.cache_resource
def _get_key_manager() -> APIKeyManager:
    """Retorna instância singleton do gerenciador."""
    return APIKeyManager()


def key_manager() -> APIKeyManager:
    """
    Interface pública para obter o gerenciador de keys.
    
    Uso:
        from key_manager import key_manager
        km = key_manager()
        claude_key = km.get_claude_key()
    """
    return _get_key_manager()


# ── Helpers rápidos ─────────────────────────────────────────────────────

def get_claude_key() -> str:
    """Atalho: `from key_manager import get_claude_key`"""
    return key_manager().get_claude_key()


def get_gemini_key() -> str:
    """Atalho: `from key_manager import get_gemini_key`"""
    return key_manager().get_gemini_key()


# ── Debug ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    km = key_manager()
    print("\n=== Key Manager Status ===")
    print(km.status())
    print("\n✅ Key Manager carregado com sucesso!")