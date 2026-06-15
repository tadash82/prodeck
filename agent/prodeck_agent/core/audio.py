"""Atalhos de mídia (mutar, volume) com o comando certo pro backend de áudio
da máquina — PipeWire (`wpctl`) ou PulseAudio (`pactl`).

O front não consegue detectar binários; então o agente monta os comandos e os
expõe (via `/presets`, junto com `system.py`) pro editor oferecer botões prontos
sem o usuário adivinhar a ferramenta. Mesma detecção do `state.py` (lê o mute).
"""

import shutil

# Passo de volume por toque (5%). `wpctl` aceita "5%+"/"5%-"; `pactl`, "+5%"/"-5%".
_STEP = 5


def audio_backend() -> str | None:
    """`"wpctl"` (PipeWire) ou `"pactl"` (PulseAudio), o que existir; senão None."""
    if shutil.which("wpctl"):
        return "wpctl"
    if shutil.which("pactl"):
        return "pactl"
    return None


def audio_presets() -> list[dict]:
    """Botões prontos de mídia pro backend detectado — vazio se não houver áudio.

    Cada preset traz `label`, `icon`, `color`, `command` (lista, roda sem shell)
    e `state` (indicador que acende quando mudo), pronto pro editor preencher.
    """
    backend = audio_backend()
    if backend == "wpctl":
        sink, source = "@DEFAULT_AUDIO_SINK@", "@DEFAULT_AUDIO_SOURCE@"
        cmds = {
            "mute_sink": ["wpctl", "set-mute", sink, "toggle"],
            "vol_up": ["wpctl", "set-volume", "-l", "1.5", sink, f"{_STEP}%+"],
            "vol_down": ["wpctl", "set-volume", sink, f"{_STEP}%-"],
            "mute_source": ["wpctl", "set-mute", source, "toggle"],
        }
    elif backend == "pactl":
        sink, source = "@DEFAULT_SINK@", "@DEFAULT_SOURCE@"
        cmds = {
            "mute_sink": ["pactl", "set-sink-mute", sink, "toggle"],
            "vol_up": ["pactl", "set-sink-volume", sink, f"+{_STEP}%"],
            "vol_down": ["pactl", "set-sink-volume", sink, f"-{_STEP}%"],
            "mute_source": ["pactl", "set-source-mute", source, "toggle"],
        }
    else:
        return []

    return [
        {
            "label": "Mute Som",
            "icon": "mdi:volume-mute",
            "color": "#3b82f6",
            "command": cmds["mute_sink"],
            "state": "audio_muted",
        },
        {
            "label": "Volume +",
            "icon": "mdi:volume-plus",
            "color": "#22c55e",
            "command": cmds["vol_up"],
            "state": None,
        },
        {
            "label": "Volume −",
            "icon": "mdi:volume-minus",
            "color": "#f59e0b",
            "command": cmds["vol_down"],
            "state": None,
        },
        {
            "label": "Mute Mic",
            "icon": "mdi:microphone-off",
            "color": "#ec4899",
            "command": cmds["mute_source"],
            "state": "mic_muted",
        },
    ]
