"""Abre um programa: lista de argumentos, sem shell — sem injeção de comando.

Com `focus_if_open`, antes de lançar tenta trazer para frente uma janela já
aberta do mesmo app (X11/EWMH) — assim um app minimizado volta com um toque em
vez de abrir outra instância. Se nada casar, lança normalmente (fallback seguro).
"""

import os
import subprocess

from ..models import OpenAppAction


def _match_from_command(command: list[str]) -> str:
    """Termo para casar a janela: o nome do binário (basename de command[0])."""
    return os.path.basename(command[0].rstrip("/"))


def execute(action: OpenAppAction) -> None:
    if action.focus_if_open:
        from ..platform import current

        match = _match_from_command(action.command)
        if match and current().focus_window(match):
            return  # janela existente trazida para frente; não lança outra

    command = [
        os.path.expanduser(arg) if arg.startswith("~") else arg
        for arg in action.command
    ]
    try:
        subprocess.Popen(
            command,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        raise RuntimeError(f"programa não encontrado: {command[0]}") from None
