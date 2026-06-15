import asyncio

from prodeck_agent.core import state as state_mod
from prodeck_agent.core.config import ConfigStore
from prodeck_agent.core.models import (
    AutoProfileRule,
    DeckConfig,
    Page,
    Profile,
)
from prodeck_agent.core.state import StateWatcher
from prodeck_agent.core.window import match_profile


class FakeConnections:
    def __init__(self) -> None:
        self.active = {object()}  # "tem alguém conectado"
        self.sent: list = []

    async def broadcast(self, message, exclude=None) -> None:
        self.sent.append(message)


class FakePlatform:
    """Provider falso: fixa a janela ativa para o teste do perfil automático."""

    def __init__(self, window) -> None:
        self._window = window

    def active_window(self):
        return self._window


def _patch_window(monkeypatch, window) -> None:
    monkeypatch.setattr(state_mod, "current", lambda: FakePlatform(window))


def _config() -> DeckConfig:
    return DeckConfig(
        active_profile="geral",
        profiles=[
            Profile(id="geral", name="Geral", pages=[Page(id="p", name="P")]),
            Profile(id="dev", name="Dev", pages=[Page(id="p", name="P")]),
        ],
        auto_profile=[AutoProfileRule(match="code", profile="dev")],
    )


def test_match_profile_by_class_or_title():
    rules = [AutoProfileRule(match="code", profile="dev")]
    assert match_profile(rules, "Code", "projeto") == "dev"
    assert match_profile(rules, "firefox", "pull request - github") is None
    assert match_profile(rules, "firefox", "abrir no Code agora") == "dev"
    assert match_profile([], "Code", "x") is None


def test_watcher_switches_profile_on_matching_window(tmp_path, monkeypatch):
    store = ConfigStore(tmp_path)
    store.save_config(_config())
    conns = FakeConnections()
    watcher = StateWatcher(store, conns)

    _patch_window(monkeypatch, ("Code", "projeto"))
    asyncio.run(watcher.check_active_window())

    assert store.load_config().active_profile == "dev"
    assert conns.sent and conns.sent[-1].id == "auto-profile"
    assert conns.sent[-1].payload.active_profile == "dev"


def test_watcher_ignores_when_no_rule_matches(tmp_path, monkeypatch):
    store = ConfigStore(tmp_path)
    store.save_config(_config())
    conns = FakeConnections()
    watcher = StateWatcher(store, conns)

    _patch_window(monkeypatch, ("firefox", "github"))
    asyncio.run(watcher.check_active_window())

    assert store.load_config().active_profile == "geral"
    assert conns.sent == []


def test_watcher_does_not_refire_same_window(tmp_path, monkeypatch):
    store = ConfigStore(tmp_path)
    store.save_config(_config())
    conns = FakeConnections()
    watcher = StateWatcher(store, conns)
    _patch_window(monkeypatch, ("Code", "x"))

    asyncio.run(watcher.check_active_window())
    asyncio.run(watcher.check_active_window())  # mesma janela: não repete
    assert len(conns.sent) == 1
