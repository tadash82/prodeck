"""Plugin do ProDeck: mutar/ensurdecer no Discord via RPC local.

Expõe os ActionPlugins (entry points em ``prodeck.actions``) e ``voice_state()``,
consumido pelo agente para acender o botão conforme o estado real do Discord.
"""

from .plugin import deaf_plugin, mute_plugin
from .rpc import voice_state

__all__ = ["deaf_plugin", "mute_plugin", "voice_state"]
