"""Janela ativa do PC (X11) para o perfil automático.

Usa Xlib (já vem com o pynput) — sem dependência nova. Só funciona em X11: em
Wayland o compositor não expõe a janela ativa por aqui, então `active_window()`
devolve `None` e o recurso fica inerte (sem erro, sem log barulhento).
"""

import os

from loguru import logger

from .models import AutoProfileRule

_display = None
_atoms: dict[str, int] = {}


def _connect() -> None:
    global _display, _atoms
    from Xlib import display

    _display = display.Display()
    _atoms = {
        "active": _display.intern_atom("_NET_ACTIVE_WINDOW"),
        "name": _display.intern_atom("_NET_WM_NAME"),
        "utf8": _display.intern_atom("UTF8_STRING"),
    }


def active_window() -> tuple[str, str] | None:
    """`(classe, título)` da janela em foco, ou `None` se indisponível.

    A conexão Xlib é reaproveitada entre chamadas; em qualquer erro (janela já
    destruída, sessão Wayland, X reiniciado) reseta para reconectar na próxima.
    """
    if not os.environ.get("DISPLAY"):
        return None
    global _display
    try:
        from Xlib import X

        if _display is None:
            _connect()
        root = _display.screen().root
        prop = root.get_full_property(_atoms["active"], X.AnyPropertyType)
        if not prop or not prop.value or not prop.value[0]:
            return None
        win = _display.create_resource_object("window", prop.value[0])
        wm_class = win.get_wm_class()
        klass = (wm_class[1] if wm_class else "") or ""
        name = win.get_full_property(_atoms["name"], _atoms["utf8"])
        title = name.value.decode("utf-8", "replace") if name else (win.get_wm_name() or "")
        return (klass, title)
    except Exception as exc:
        logger.debug("janela ativa indisponível: {}", exc)
        _display = None  # força reconexão na próxima chamada
        return None


def match_profile(rules: list[AutoProfileRule], klass: str, title: str) -> str | None:
    """Primeiro perfil cujo `match` aparece na classe ou no título (case-insensitive)."""
    haystack = f"{klass} {title}".lower()
    for rule in rules:
        if rule.match.lower() in haystack:
            return rule.profile
    return None
