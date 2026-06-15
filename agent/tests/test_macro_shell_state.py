import asyncio
import json
import time

from prodeck_agent.core import state as state_module
from prodeck_agent.core.engine import ActionEngine
from prodeck_agent.core.models import (
    DelayStep,
    MacroAction,
    OpenUrlAction,
    ShellAction,
    TextAction,
)
from prodeck_agent.core.state import StateWatcher
from tests.test_ws import build_client, hello


def run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------- macro

def test_macro_runs_steps_in_order_with_delay():
    engine = ActionEngine()
    calls = []
    engine.register("open_url", lambda a: calls.append(a.url))
    macro = MacroAction(
        steps=[
            OpenUrlAction(url="https://a.com"),
            DelayStep(ms=50),
            OpenUrlAction(url="https://b.com"),
        ]
    )
    started = time.perf_counter()
    ok, message = run(engine.run(macro))
    elapsed = time.perf_counter() - started
    assert ok and message == ""
    assert calls == ["https://a.com", "https://b.com"]
    assert elapsed >= 0.05


def test_macro_stops_at_failing_step_and_names_it():
    engine = ActionEngine()
    calls = []

    def boom(action):
        raise RuntimeError("quebrou")

    engine.register("open_url", boom)
    engine.register("text", lambda a: calls.append(a.text))
    macro = MacroAction(
        steps=[OpenUrlAction(url="https://a.com"), TextAction(text="nunca")]
    )
    ok, message = run(engine.run(macro))
    assert not ok
    assert "passo 1" in message and "quebrou" in message
    assert calls == []


# ---------------------------------------------------------------- shell gate

def test_shell_blocked_by_default():
    engine = ActionEngine()
    engine.register("shell", lambda a: None)
    ok, message = run(engine.run(ShellAction(command="echo oi")))
    assert not ok and "desativadas" in message


def test_shell_runs_when_allowed():
    engine = ActionEngine()
    calls = []
    engine.register("shell", lambda a: calls.append(a.command))
    ok, _ = run(engine.run(ShellAction(command="echo oi"), allow_shell=True))
    assert ok and calls == ["echo oi"]


def test_shell_inside_macro_respects_gate():
    engine = ActionEngine()
    engine.register("shell", lambda a: None)
    macro = MacroAction(steps=[ShellAction(command="rm -rf /")])
    ok, message = run(engine.run(macro))
    assert not ok and "passo 1" in message


# ---------------------------------------------------------------- estado

def test_read_state_unknown_provider_is_false():
    assert state_module.read_state("nao-existe") is False


def test_watcher_snapshot_and_push(tmp_path, monkeypatch):
    fake_value = {"v": False}

    class FakePlatform:
        def is_muted(self, kind):
            return fake_value["v"]

    monkeypatch.setattr(state_module, "current", lambda: FakePlatform())

    sent = []

    class FakeConnections:
        async def broadcast(self, message, exclude=None):
            sent.append(json.loads(message.model_dump_json()))

    executed = []
    client, store = build_client(tmp_path, executed)
    config = store.load_config()
    config.profiles[0].pages[0].buttons[0].state = "mic_muted"
    store.save_config(config)

    watcher = StateWatcher(store, FakeConnections())

    snapshot = watcher.snapshot()
    assert len(snapshot) == 1
    assert snapshot[0].payload.active is False

    # sem mudança → nada; com mudança → broadcast
    run(watcher.push_changes())
    assert sent == []
    fake_value["v"] = True
    run(watcher.push_changes())
    assert len(sent) == 1 and sent[0]["payload"]["active"] is True


def test_deck_get_sends_state_snapshot(tmp_path, monkeypatch):
    class FakePlatform:
        def is_muted(self, kind):
            return True

    monkeypatch.setattr(state_module, "current", lambda: FakePlatform())
    client, store = build_client(tmp_path, [])
    config = store.load_config()
    config.profiles[0].pages[0].buttons[0].state = "mic_muted"
    store.save_config(config)

    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps(hello(store.pair_token())))
        ws.receive_text()
        ws.send_text(json.dumps({"type": "deck.get", "id": "2"}))
        layout = json.loads(ws.receive_text())
        assert layout["type"] == "deck.layout"
        update = json.loads(ws.receive_text())
        assert update["type"] == "state.update"
        assert update["payload"] == {"button_id": "b1", "active": True}
