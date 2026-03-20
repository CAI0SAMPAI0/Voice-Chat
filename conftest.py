import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Garante que testes podem importar voice.py sem .env configurado
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-testkey1234567890abcdef")