import asyncio
import json

from fastapi.testclient import TestClient

from prodeck_agent.core import state as state_mod
from prodeck_agent.core.config import ConfigStore
from prodeck_agent.core.engine import ActionEngine
from prodeck_agent.core.models import Button, DeckConfig, Page, Position, Profile
from prodeck_agent.core.pairing import Pairing
from prodeck_agent.core.state import StateWatcher
from prodeck_agent.core.widgets import widget_value
from prodeck_agent.server.app import create_app


class FakeConnections:
    active = {object()}

    def __init__(self) -> None:
        self.sent: list = []

    async def broadcast(self, message, exclude=None) -> None:
        self.sent.append(message)


def _store_with_widget(tmp_path, *, action=None):
    store = ConfigStore(tmp_path)
    store.save_config(
        DeckConfig(
            active_profile="t",
            profiles=[
                Profile(
                    id="t",
                    name="T",
                    pages=[
                        Page(
                            id="p",
                            name="P",
                            buttons=[
                                Button(
                                    id="w1",
                                    position=Position(col=0, row=0),
                                    label="CPU",
                                    widget="cpu",
                                    action=action,
                                )
                            ],
                        )
                    ],
                )
            ],
        )
    )
    return store


def test_widget_value_known_and_unknown():
    assert widget_value("clock")  # string não vazia (HH:MM)
    assert widget_value("inexistente") == ""


def test_watcher_widget_snapshot_and_push(tmp_path, monkeypatch):
    store = _store_with_widget(tmp_path)
    conns = FakeConnections()
    watcher = StateWatcher(store, conns)

    value = {"v": "10%"}
    monkeypatch.setattr(state_mod, "widget_value", lambda kind: value["v"])

    snapshot = watcher.widget_snapshot()
    assert len(snapshot) == 1 and snapshot[0].payload.value == "10%"

    asyncio.run(watcher.push_widget_changes())  # sem mudança → nada
    assert conns.sent == []

    value["v"] = "20%"
    asyncio.run(watcher.push_widget_changes())
    assert len(conns.sent) == 1 and conns.sent[0].payload.value == "20%"


def test_widget_only_button_triggers_noop(tmp_path):
    store = _store_with_widget(tmp_path, action=None)  # só-widget, sem ação
    app = create_app(store, ActionEngine(), Pairing(store), http_port=8710)
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        ws.send_text(
            json.dumps(
                {
                    "type": "hello",
                    "id": "1",
                    "payload": {"token": store.pair_token(), "device_id": "d", "device_name": "d"},
                }
            )
        )
        ws.receive_text()
        ws.send_text(
            json.dumps({"type": "action.trigger", "id": "2", "payload": {"button_id": "w1"}})
        )
        result = json.loads(ws.receive_text())
        assert result["payload"]["status"] == "ok"  # sem ação → no-op, sem erro
