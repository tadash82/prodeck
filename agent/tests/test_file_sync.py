import asyncio
import json
import os

from prodeck_agent.core.config import ConfigStore
from prodeck_agent.core.state import StateWatcher


class FakeConnections:
    def __init__(self):
        self.sent = []

    async def broadcast(self, message, exclude=None):
        self.sent.append(json.loads(message.model_dump_json()))


def run(coro):
    return asyncio.run(coro)


def _bump_mtime(store: ConfigStore) -> None:
    stat = store.profiles_path.stat()
    os.utime(store.profiles_path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000))


def test_manual_edit_broadcasts_layout(tmp_path):
    store = ConfigStore(tmp_path)
    config = store.load_config()
    connections = FakeConnections()
    watcher = StateWatcher(store, connections)

    # sem mudança → nada
    run(watcher.check_config_file())
    assert connections.sent == []

    # edição "à mão": muda label e regrava o arquivo diretamente
    config.profiles[0].pages[0].buttons[0].label = "Editado no VSCode"
    store.profiles_path.write_text(config.model_dump_json(), encoding="utf-8")
    _bump_mtime(store)
    run(watcher.check_config_file())
    assert len(connections.sent) == 1
    layout = connections.sent[0]
    assert layout["type"] == "deck.layout" and layout["id"] == "file-sync"
    assert (
        layout["payload"]["profiles"][0]["pages"][0]["buttons"][0]["label"]
        == "Editado no VSCode"
    )


def test_deck_save_does_not_rebroadcast(tmp_path):
    store = ConfigStore(tmp_path)
    config = store.load_config()
    connections = FakeConnections()
    watcher = StateWatcher(store, connections)

    # fluxo do deck.save: grava e marca como sincronizado
    store.save_config(config)
    watcher.mark_config_synced()
    run(watcher.check_config_file())
    assert connections.sent == []


def test_invalid_manual_edit_is_ignored_until_fixed(tmp_path):
    store = ConfigStore(tmp_path)
    valid = store.load_config()
    connections = FakeConnections()
    watcher = StateWatcher(store, connections)

    store.profiles_path.write_text("{json quebrado", encoding="utf-8")
    _bump_mtime(store)
    run(watcher.check_config_file())
    assert connections.sent == []

    store.profiles_path.write_text(valid.model_dump_json(), encoding="utf-8")
    _bump_mtime(store)
    run(watcher.check_config_file())
    assert len(connections.sent) == 1
