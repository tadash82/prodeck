"""Abstração por sistema operacional.

O resto do core não fala diretamente com `wpctl`, `.desktop` ou Xlib — fala com
`current()`, que devolve o provider do SO. Linux é completo; Windows é
best-effort (precisa validação numa máquina Windows). Ver `base.Platform`.
"""

from .base import Platform, current

__all__ = ["Platform", "current"]
