"""Digita um texto como se fosse no teclado (snippets).

Mesma limitação do hotkey: pynput exige X11/Windows/macOS.
"""

from ..models import TextAction


def execute(action: TextAction) -> None:
    from pynput import keyboard

    keyboard.Controller().type(action.text)
