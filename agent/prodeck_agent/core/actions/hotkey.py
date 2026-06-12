"""Injeção de atalhos de teclado via pynput.

Funciona em X11, Windows e macOS. Em Wayland a injeção global é bloqueada
pelo compositor — caminho futuro: ydotool/portal (docs/02, nota X11/Wayland).
O import do pynput é tardio porque exige sessão gráfica (e quebraria testes).
"""

from ..models import HotkeyAction

_ALIASES = {
    "control": "ctrl",
    "super": "cmd",
    "win": "cmd",
    "meta": "cmd",
    "return": "enter",
    "escape": "esc",
    "prtsc": "print_screen",
    "printscreen": "print_screen",
}


def execute(action: HotkeyAction) -> None:
    from pynput import keyboard

    def to_key(name: str):
        name = name.strip().lower()
        if len(name) == 1:
            return name
        attr = _ALIASES.get(name, name)
        try:
            return getattr(keyboard.Key, attr)
        except AttributeError:
            raise RuntimeError(f"tecla desconhecida: '{name}'") from None

    keys = [to_key(k) for k in action.keys]
    controller = keyboard.Controller()
    for key in keys:
        controller.press(key)
    for key in reversed(keys):
        controller.release(key)
