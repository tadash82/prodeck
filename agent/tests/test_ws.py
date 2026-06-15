import json

from fastapi.testclient import TestClient

from prodeck_agent.core.config import ConfigStore
from prodeck_agent.core.engine import ActionEngine
from prodeck_agent.core.models import (
    Button,
    DeckConfig,
    OpenUrlAction,
    Page,
    Position,
    Profile,
)
from prodeck_agent.core.pairing import Pairing
from prodeck_agent.server.app import create_app


def build_client(tmp_path, executed):
    store = ConfigStore(tmp_path)
    store.save_config(
        DeckConfig(
            active_profile="t",
            profiles=[
                Profile(
                    id="t",
                    name="Teste",
                    pages=[
                        Page(
                            id="p1",
                            name="P1",
                            buttons=[
                                Button(
                                    id="b1",
                                    position=Position(col=0, row=0),
                                    label="Site",
                                    action=OpenUrlAction(url="https://example.com"),
                                )
                            ],
                        )
                    ],
                )
            ],
        )
    )
    engine = ActionEngine()
    engine.register("open_url", executed.append)
    app = create_app(store, engine, Pairing(store), http_port=8710)
    return TestClient(app), store


def hello(token, msg_id="1"):
    return {
        "type": "hello",
        "id": msg_id,
        "payload": {"token": token, "device_id": "dev-1", "device_name": "Teste"},
    }


def test_hello_with_valid_token(tmp_path):
    client, store = build_client(tmp_path, [])
    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps(hello(store.pair_token())))
        reply = json.loads(ws.receive_text())
        assert reply["type"] == "hello.ok"
        assert reply["payload"]["active_profile"] == "t"
    devices = store.load_devices()
    assert "dev-1" in devices.devices


def test_hello_with_invalid_token(tmp_path):
    client, _ = build_client(tmp_path, [])
    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps(hello("token-errado")))
        reply = json.loads(ws.receive_text())
        assert reply["type"] == "hello.denied"
        assert reply["payload"]["reason"] == "invalid-token"


def test_message_before_hello_is_denied(tmp_path):
    client, _ = build_client(tmp_path, [])
    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps({"type": "ping", "id": "1"}))
        reply = json.loads(ws.receive_text())
        assert reply["type"] == "hello.denied"
        assert reply["payload"]["reason"] == "not-authenticated"


def test_deck_get_and_action_trigger(tmp_path):
    executed = []
    client, store = build_client(tmp_path, executed)
    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps(hello(store.pair_token())))
        ws.receive_text()

        ws.send_text(json.dumps({"type": "deck.get", "id": "2"}))
        layout = json.loads(ws.receive_text())
        assert layout["type"] == "deck.layout"
        assert layout["payload"]["profiles"][0]["pages"][0]["buttons"][0]["id"] == "b1"

        ws.send_text(
            json.dumps({"type": "action.trigger", "id": "3", "payload": {"button_id": "b1"}})
        )
        result = json.loads(ws.receive_text())
        assert result["payload"]["status"] == "ok"
        assert len(executed) == 1

        ws.send_text(
            json.dumps({"type": "action.trigger", "id": "4", "payload": {"button_id": "zz"}})
        )
        result = json.loads(ws.receive_text())
        assert result["payload"]["status"] == "error"


def test_action_test_runs_without_saving(tmp_path):
    executed = []
    client, store = build_client(tmp_path, executed)
    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps(hello(store.pair_token())))
        ws.receive_text()

        ws.send_text(
            json.dumps(
                {
                    "type": "action.test",
                    "id": "5",
                    "payload": {"action": {"type": "open_url", "url": "https://example.com"}},
                }
            )
        )
        result = json.loads(ws.receive_text())
        assert result["type"] == "action.result"
        assert result["payload"]["button_id"] == "__test__"
        assert result["payload"]["status"] == "ok"
        assert len(executed) == 1


def test_ping_pong_and_invalid_message(tmp_path):
    client, store = build_client(tmp_path, [])
    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps(hello(store.pair_token())))
        ws.receive_text()

        ws.send_text(json.dumps({"type": "ping", "id": "9"}))
        assert json.loads(ws.receive_text())["type"] == "pong"

        ws.send_text("{nem json}")
        assert json.loads(ws.receive_text())["type"] == "error"
