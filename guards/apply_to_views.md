# Como aplicar page_guard em cada view

Adicione em cada arquivo de view — UMA linha no topo da função:

## tati_views/voice.py
```python
from guards.page_guard import page_guard, inject_anti_flash

@page_guard
def show_voice() -> None:
    # ... resto igual
```

## tati_views/history.py
```python
from guards.page_guard import page_guard, scroll_restore

@page_guard
def show_history() -> None:
    scroll_restore()   # substitui o bloco CSS repetido de overflow
    # ... resto igual
```

## tati_views/settings.py
```python
from guards.page_guard import page_guard, scroll_restore

@page_guard
def show_settings() -> None:
    scroll_restore()
    # ... resto igual
```

## tati_views/dashboard.py
```python
from guards.page_guard import page_guard, scroll_restore

@page_guard
def show_dashboard() -> None:
    scroll_restore()
    # ... resto igual
```

## tati_views/login.py
```python
# Login NÃO usa @page_guard (não precisa estar logado)
# Mas usa inject_anti_flash para evitar o flash do card
from guards.page_guard import inject_anti_flash

def show_login() -> None:
    inject_anti_flash()
    # ... resto igual
```
