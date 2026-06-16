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
        "client_list": _display.intern_atom("_NET_CLIENT_LIST"),
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


def focus_window(match: str) -> bool:
    """Traz para frente (desminimiza + foca) a primeira janela já aberta cuja
    classe ou título contenha `match` (case-insensitive).

    Devolve True se achou e ativou; False se não há janela correspondente ou a
    sessão não expõe X (Wayland/headless). Usa o protocolo EWMH `_NET_ACTIVE_
    WINDOW` (fonte=pager) que o Mutter/GNOME honra mesmo para janela minimizada.
    """
    if not os.environ.get("DISPLAY") or not match.strip():
        return False
    needle = match.strip().lower()
    global _display
    try:
        from Xlib import X, protocol

        if _display is None:
            _connect()
        root = _display.screen().root
        prop = root.get_full_property(_atoms["client_list"], X.AnyPropertyType)
        if not prop or not prop.value:
            return False
        for wid in prop.value:
            win = _display.create_resource_object("window", wid)
            wm_class = win.get_wm_class()  # (instância, classe)
            klass = " ".join(c for c in (wm_class or ()) if c)
            name = win.get_full_property(_atoms["name"], _atoms["utf8"])
            title = name.value.decode("utf-8", "replace") if name else (win.get_wm_name() or "")
            if needle not in f"{klass} {title}".lower():
                continue
            event = protocol.event.ClientMessage(
                window=win,
                client_type=_atoms["active"],
                data=(32, [2, X.CurrentTime, 0, 0, 0]),  # fonte=2 (pager)
            )
            mask = X.SubstructureRedirectMask | X.SubstructureNotifyMask
            root.send_event(event, event_mask=mask)
            _display.flush()
            return True
        return False
    except Exception as exc:
        logger.debug("focar janela falhou: {}", exc)
        _display = None  # força reconexão na próxima chamada
        return False


def match_profile(rules: list[AutoProfileRule], klass: str, title: str) -> str | None:
    """Primeiro perfil cujo `match` aparece na classe ou no título (case-insensitive)."""
    haystack = f"{klass} {title}".lower()
    for rule in rules:
        if rule.match.lower() in haystack:
            return rule.profile
    return None
