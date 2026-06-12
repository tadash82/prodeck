"""Estado ao vivo dos botões (toggle): providers e watcher de mudanças.

Um botão com `state` definido reflete um fato do sistema (ex.: mic mutado).
O watcher avalia os providers em uso e faz broadcast de `state.update`
quando algo muda — e imediatamente após cada ação disparada.
"""

import asyncio
import shutil
import subprocess
from collections.abc import Callable

from loguru import logger

from .models import StateUpdateMessage, StateUpdatePayload


def _muted(kind: str) -> bool:
    """kind: "source" (microfone) ou "sink" (áudio de saída).

    Tenta wpctl (PipeWire, padrão no Ubuntu atual) e cai para pactl (PulseAudio).
    """
    if shutil.which("wpctl"):
        target = "@DEFAULT_AUDIO_SOURCE@" if kind == "source" else "@DEFAULT_AUDIO_SINK@"
        out = subprocess.run(
            ["wpctl", "get-volume", target], capture_output=True, text=True, timeout=2
        )
        return "[MUTED]" in out.stdout
    if shutil.which("pactl"):
        target = "@DEFAULT_SOURCE@" if kind == "source" else "@DEFAULT_SINK@"
        out = subprocess.run(
            ["pactl", f"get-{kind}-mute", target],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return "yes" in out.stdout.lower() or "sim" in out.stdout.lower()
    return False


PROVIDERS: dict[str, Callable[[], bool]] = {
    "mic_muted": lambda: _muted("source"),
    "audio_muted": lambda: _muted("sink"),
}


def read_state(provider: str) -> bool:
    fn = PROVIDERS.get(provider)
    if fn is None:
        return False
    try:
        return fn()
    except Exception:
        return False


class StateWatcher:
    POLL_SECONDS = 3.0

    def __init__(self, store, connections) -> None:
        self.store = store
        self.connections = connections
        self._last: dict[str, bool] = {}
        # refs fortes: create_task sem ref pode ser coletado no meio do sleep
        self._pending: set[asyncio.Task] = set()

    def push_soon(self, delay: float = 0.25) -> None:
        """Agenda um push fora do loop de mensagens (Popen ainda aplicando)."""

        async def delayed() -> None:
            await asyncio.sleep(delay)
            await self.push_changes()

        task = asyncio.create_task(delayed())
        self._pending.add(task)
        task.add_done_callback(self._pending.discard)

    def _stateful_buttons(self):
        config = self.store.load_config()
        for profile in config.profiles:
            for page in profile.pages:
                for button in page.buttons:
                    if button.state is not None:
                        yield button

    def snapshot(self) -> list[StateUpdateMessage]:
        """Estado atual de todos os botões com state — para clientes recém-conectados."""
        messages = []
        for button in self._stateful_buttons():
            active = read_state(button.state)
            self._last[button.id] = active
            messages.append(
                StateUpdateMessage(
                    id="state",
                    payload=StateUpdatePayload(button_id=button.id, active=active),
                )
            )
        return messages

    async def push_changes(self) -> None:
        """Broadcast apenas do que mudou desde a última avaliação."""
        for button in self._stateful_buttons():
            active = read_state(button.state)
            if self._last.get(button.id) == active:
                continue
            self._last[button.id] = active
            await self.connections.broadcast(
                StateUpdateMessage(
                    id="state",
                    payload=StateUpdatePayload(button_id=button.id, active=active),
                )
            )

    async def run(self) -> None:
        while True:
            try:
                await self.push_changes()
            except Exception as exc:
                logger.warning("watcher de estado: {}", exc)
            await asyncio.sleep(self.POLL_SECONDS)
