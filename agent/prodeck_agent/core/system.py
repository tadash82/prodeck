"""Comandos de sistema confiáveis (bloquear tela, print) detectados na máquina.

Esses são justamente os casos em que um atalho de teclado *global* (super+l,
PrintScreen) não funciona via injeção do pynput — o compositor captura a tecla
por keycode (ver actions/hotkey.py). Rodar o comando direto é determinístico.
"""

import shutil


def lock_command() -> list[str] | None:
    """Comando pra bloquear a tela — o que existir na máquina, senão None."""
    if shutil.which("loginctl"):
        return ["loginctl", "lock-session"]
    if shutil.which("xdg-screensaver"):
        return ["xdg-screensaver", "lock"]
    if shutil.which("gnome-screensaver-command"):
        return ["gnome-screensaver-command", "-l"]
    return None


def screenshot_command() -> list[str] | None:
    """Comando pra tirar print (interativo quando dá), senão None."""
    if shutil.which("gnome-screenshot"):
        return ["gnome-screenshot", "-i"]
    if shutil.which("spectacle"):
        return ["spectacle"]
    if shutil.which("flameshot"):
        return ["flameshot", "gui"]
    if shutil.which("grim"):  # Wayland
        return ["grim"]
    if shutil.which("scrot"):
        return ["scrot"]
    return None


def system_presets() -> list[dict]:
    """Atalhos prontos de sistema pro editor — só os que a máquina suporta."""
    presets: list[dict] = []
    lock = lock_command()
    if lock:
        presets.append(
            {
                "label": "Bloquear",
                "icon": "mdi:lock",
                "color": "#ef4444",
                "command": lock,
                "state": None,
            }
        )
    shot = screenshot_command()
    if shot:
        presets.append(
            {
                "label": "Print",
                "icon": "mdi:camera",
                "color": "#8b5cf6",
                "command": shot,
                "state": None,
            }
        )
    return presets
