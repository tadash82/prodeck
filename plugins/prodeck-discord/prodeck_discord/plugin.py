"""Ações de plugin do ProDeck para mutar/ensurdecer no Discord via RPC.

Dois plugins separados (sem campos) para aparecerem prontos no editor como
ações de um toque. Cada `run` inverte o estado real lido do Discord e levanta
exceção em falha — o engine do agente roda isso numa thread.
"""

from prodeck_agent.core.plugins import ActionPlugin

from .rpc import client

DISCORD_BLURPLE = "#5865F2"


def _toggle_mute(_params: dict) -> None:
    client().toggle("mute")


def _toggle_deaf(_params: dict) -> None:
    client().toggle("deaf")


mute_plugin = ActionPlugin(
    name="discord_mute",
    label="Discord: Mutar mic",
    icon="mdi:microphone-off",
    color=DISCORD_BLURPLE,
    run=_toggle_mute,
)

deaf_plugin = ActionPlugin(
    name="discord_deaf",
    label="Discord: Ensurdecer",
    icon="mdi:headphones-off",
    color=DISCORD_BLURPLE,
    run=_toggle_deaf,
)
