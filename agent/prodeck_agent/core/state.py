"""Watcher do agente: estado ao vivo dos botões e mudanças da config no disco.

Um botão com `state` definido reflete um fato do sistema (ex.: mic mutado);
o watcher avalia os providers em uso e faz broadcast de `state.update` quando
algo muda — e imediatamente após cada ação disparada. O mesmo loop observa o
mtime do profiles.json: edições feitas à mão (VSCode etc.) são propagadas a
todos os dispositivos como `deck.layout`.
"""

import asyncio

from loguru import logger

from .models import (
    DeckLayoutMessage,
    StateUpdateMessage,
    StateUpdatePayload,
    WidgetUpdateMessage,
    WidgetUpdatePayload,
)
from .platform import current
from .widgets import widget_value
from .window import match_profile

# provider do botão → "lado" do áudio que o SO consulta
_STATE_KIND = {"mic_muted": "source", "audio_muted": "sink"}


def read_state(provider: str) -> bool:
    kind = _STATE_KIND.get(provider)
    return current().is_muted(kind) if kind else False


class StateWatcher:
    POLL_SECONDS = 2.0

    def __init__(self, store, connections) -> None:
        self.store = store
        self.connections = connections
        self._last: dict[str, bool] = {}
        self._last_widget: dict[str, str] = {}
        self._config_mtime = store.mtime()
        self._last_window: tuple[str, str] | None = None
        # refs fortes: create_task sem ref pode ser coletado no meio do sleep
        self._pending: set[asyncio.Task] = set()

    # ------------------------------------------------- config no disco

    def mark_config_synced(self) -> None:
        """Chamado após um deck.save — aquela escrita não é 'edição à mão'."""
        self._config_mtime = self.store.mtime()

    async def check_config_file(self) -> None:
        mtime = self.store.mtime()
        if mtime == self._config_mtime:
            return
        self._config_mtime = mtime
        try:
            config = self.store.load_config()
        except RuntimeError as exc:
            logger.warning("profiles.json editado à mão está inválido: {}", exc)
            return
        self._config_mtime = self.store.mtime()
        logger.info("profiles.json mudou no disco — propagando aos dispositivos")
        await self.connections.broadcast(
            DeckLayoutMessage(id="file-sync", payload=config)
        )

    # ------------------------------------------------- perfil automático

    async def check_active_window(self) -> None:
        """Se houver regras e a janela em foco mudou, troca o perfil ativo.

        Só age na **mudança** de janela (não fica brigando com troca manual do
        usuário enquanto ele segue no mesmo app) e só quando a regra aponta para
        um perfil existente e diferente do atual. Persiste e propaga como
        `deck.layout` com `id: "auto-profile"`.
        """
        if not self.connections.active:
            return  # ninguém conectado: nada a propagar, evita IO/disco à toa
        config = self.store.load_config()
        if not config.auto_profile:
            return
        window = current().active_window()
        if window is None or window == self._last_window:
            return
        self._last_window = window
        target = match_profile(config.auto_profile, *window)
        if target is None or target == config.active_profile:
            return
        if not any(p.id == target for p in config.profiles):
            return  # regra aponta para um perfil que não existe (mais)
        config.active_profile = target
        self.store.save_config(config)
        self.mark_config_synced()
        logger.info("perfil automático: janela '{}' → perfil '{}'", window[0], target)
        await self.connections.broadcast(
            DeckLayoutMessage(id="auto-profile", payload=config)
        )

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

    # ------------------------------------------------- widgets (dado ao vivo)

    def _widget_buttons(self):
        for profile in self.store.load_config().profiles:
            for page in profile.pages:
                for button in page.buttons:
                    if button.widget is not None:
                        yield button

    def widget_snapshot(self) -> list[WidgetUpdateMessage]:
        """Valor atual de cada botão-widget — para clientes recém-conectados."""
        messages = []
        for button in self._widget_buttons():
            value = widget_value(button.widget)
            self._last_widget[button.id] = value
            messages.append(
                WidgetUpdateMessage(
                    id="widget", payload=WidgetUpdatePayload(button_id=button.id, value=value)
                )
            )
        return messages

    async def push_widget_changes(self) -> None:
        for button in self._widget_buttons():
            value = widget_value(button.widget)
            if self._last_widget.get(button.id) == value:
                continue
            self._last_widget[button.id] = value
            await self.connections.broadcast(
                WidgetUpdateMessage(
                    id="widget", payload=WidgetUpdatePayload(button_id=button.id, value=value)
                )
            )

    async def run(self) -> None:
        while True:
            try:
                await self.check_config_file()
                await self.check_active_window()
                await self.push_changes()
                await self.push_widget_changes()
            except Exception as exc:
                logger.warning("watcher: {}", exc)
            await asyncio.sleep(self.POLL_SECONDS)
