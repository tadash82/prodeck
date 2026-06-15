"""Widgets: o texto ao vivo que um botão exibe (CPU, RAM, relógio…).

Os tipos genéricos (relógio/data) usam só a stdlib; os de sistema (cpu/ram)
passam pela camada de plataforma (`platform.current()`), então ganham suporte a
um SO novo junto com o provider. Disco usa `shutil` (cross-platform).
"""

import os
import shutil
from collections.abc import Callable
from datetime import datetime

from .platform import current


def _clock() -> str:
    return datetime.now().strftime("%H:%M")


def _date() -> str:
    return datetime.now().strftime("%d/%m")


def _datetime() -> str:
    return datetime.now().strftime("%d/%m %H:%M")


def _cpu() -> str:
    pct = current().cpu_percent()
    return f"{pct:.0f}%" if pct is not None else "—"


def _ram() -> str:
    info = current().mem_info()
    return f"{info[0]:.1f}/{info[1]:.0f} GB" if info else "—"


def _disk() -> str:
    try:
        usage = shutil.disk_usage(os.path.expanduser("~"))
        return f"{100 * usage.used / usage.total:.0f}%"
    except Exception:
        return "—"


WIDGETS: dict[str, Callable[[], str]] = {
    "clock": _clock,
    "date": _date,
    "datetime": _datetime,
    "cpu": _cpu,
    "ram": _ram,
    "disk": _disk,
}


def widget_value(kind: str) -> str:
    """Texto atual do widget; string vazia para um tipo desconhecido."""
    fn = WIDGETS.get(kind)
    if fn is None:
        return ""
    try:
        return fn()
    except Exception:
        return "—"
