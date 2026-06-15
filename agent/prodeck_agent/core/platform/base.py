"""Interface por SO: o que difere entre Linux/Windows/macOS fica atrás daqui.

Cada provider implementa o mesmo contrato; os consumidores (endpoints `/presets`
e `/apps`, o `StateWatcher`, o `default_config`) só conhecem esta interface. Para
suportar um SO novo: escreva um provider e registre em `current()` — nada no core
muda.
"""

import sys
from typing import Protocol


class Platform(Protocol):
    """Tudo que depende do sistema operacional. Todos os métodos devem ser
    tolerantes: na ausência da ferramenta, devolvem vazio/None (sem levantar)."""

    name: str

    def presets(self) -> list[dict]:
        """Atalhos prontos (mídia, bloquear, print…) já com o comando do SO."""
        ...

    def installed_apps(self) -> list[dict]:
        """Apps instalados `{name, exec, icon}` para o seletor do editor."""
        ...

    def active_window(self) -> tuple[str, str] | None:
        """`(classe, título)` da janela em foco, ou `None` se indisponível."""
        ...

    def is_muted(self, kind: str) -> bool:
        """`kind`: `"source"` (microfone) ou `"sink"` (saída de áudio)."""
        ...

    def starter_buttons(self) -> list[dict]:
        """Botões iniciais específicos do SO (terminal, bloquear, mutar mic),
        cada um `{label, icon, color, action, state}` com `action` como dict."""
        ...


_current: Platform | None = None


def current() -> Platform:
    """Provider do SO atual (memoizado). win32 → Windows; o resto → Linux."""
    global _current
    if _current is None:
        if sys.platform == "win32":
            from .windows import WindowsPlatform

            _current = WindowsPlatform()
        else:
            # Linux é o alvo principal; macOS cairia aqui e usaria o que der
            # (xdg/Xlib não existem — os métodos degradam para vazio/None).
            from .linux import LinuxPlatform

            _current = LinuxPlatform()
    return _current
