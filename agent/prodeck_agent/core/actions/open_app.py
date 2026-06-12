"""Abre um programa: lista de argumentos, sem shell — sem injeção de comando."""

import os
import subprocess

from ..models import OpenAppAction


def execute(action: OpenAppAction) -> None:
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
