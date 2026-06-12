"""Abre pasta ou arquivo no aplicativo padrão do sistema."""

import os
import subprocess
import sys
from pathlib import Path

from ..models import OpenPathAction


def execute(action: OpenPathAction) -> None:
    path = Path(action.path).expanduser()
    if not path.exists():
        raise RuntimeError(f"caminho não existe: {path}")

    if sys.platform == "win32":
        os.startfile(path)
        return

    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.Popen(
        [opener, str(path)],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
