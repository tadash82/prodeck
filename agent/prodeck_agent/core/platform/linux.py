"""Provider de Linux (X11/PipeWire/XDG) — implementação completa e validada.

Compõe os módulos já existentes (`audio`, `system`, `apps`, `window`) na
interface `Platform`. É a referência do que um provider novo precisa entregar.
"""

import shutil
import subprocess

from ..apps import list_apps
from ..audio import audio_presets
from ..system import lock_command, system_presets
from ..window import active_window

_TERMINALS = (
    "gnome-terminal",
    "konsole",
    "xfce4-terminal",
    "tilix",
    "ptyxis",
    "x-terminal-emulator",
    "xterm",
)


def _mic_mute_command() -> list[str] | None:
    if shutil.which("wpctl"):
        return ["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "toggle"]
    if shutil.which("pactl"):
        return ["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "toggle"]
    return None


def _is_muted(kind: str) -> bool:
    """`kind`: "source" (mic) ou "sink" (saída). Tenta wpctl e cai p/ pactl."""
    if shutil.which("wpctl"):
        target = "@DEFAULT_AUDIO_SOURCE@" if kind == "source" else "@DEFAULT_AUDIO_SINK@"
        out = subprocess.run(
            ["wpctl", "get-volume", target], capture_output=True, text=True, timeout=2
        )
        return "[MUTED]" in out.stdout
    if shutil.which("pactl"):
        target = "@DEFAULT_SOURCE@" if kind == "source" else "@DEFAULT_SINK@"
        out = subprocess.run(
            ["pactl", f"get-{kind}-mute", target], capture_output=True, text=True, timeout=2
        )
        return "yes" in out.stdout.lower() or "sim" in out.stdout.lower()
    return False


class LinuxPlatform:
    name = "linux"

    def presets(self) -> list[dict]:
        return audio_presets() + system_presets()

    def installed_apps(self) -> list[dict]:
        return list_apps()

    def active_window(self) -> tuple[str, str] | None:
        return active_window()

    def is_muted(self, kind: str) -> bool:
        try:
            return _is_muted(kind)
        except Exception:
            return False

    def starter_buttons(self) -> list[dict]:
        buttons: list[dict] = []
        term = next((t for t in _TERMINALS if shutil.which(t)), None)
        buttons.append(
            {
                "label": "Terminal",
                "icon": "mdi:console",
                "color": "#22c55e",
                # comando direto (o atalho global ctrl+alt+t não dispara via pynput)
                "action": (
                    {"type": "open_app", "command": [term]}
                    if term
                    else {"type": "hotkey", "keys": ["ctrl", "alt", "t"]}
                ),
                "state": None,
            }
        )
        lock = lock_command()
        buttons.append(
            {
                "label": "Bloquear",
                "icon": "mdi:lock",
                "color": "#ef4444",
                "action": (
                    {"type": "open_app", "command": lock}
                    if lock
                    else {"type": "hotkey", "keys": ["super", "l"]}
                ),
                "state": None,
            }
        )
        mic = _mic_mute_command()
        if mic:
            buttons.append(
                {
                    "label": "Mute Mic",
                    "icon": "mdi:microphone-off",
                    "color": "#ec4899",
                    "action": {"type": "open_app", "command": mic},
                    "state": "mic_muted",
                }
            )
        return buttons
