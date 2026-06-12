import json

import pytest
from pydantic import ValidationError

from prodeck_agent.core.models import (
    Button,
    DeckConfig,
    OpenPathAction,
    Page,
    Position,
    Profile,
)
from tests.test_ws import build_client, hello


def make_config(label="Nova"):
    return {
        "version": 1,
        "active_profile": "t",
        "profiles": [
            {
                "id": "t",
                "name": "Teste",
                "pages": [
                    {
                        "id": "p1",
                        "name": "P1",
                        "grid": {"cols": 3, "rows": 4},
                        "buttons": [
                            {
                                "id": "b-novo",
                                "position": {"col": 1, "row": 1},
                                "label": label,
                                "icon": "mdi:folder",
                                "color": "#f59e0b",
                                "action": {"type": "open_path", "path": "~"},
                            }
                        ],
                    }
                ],
            }
        ],
    }


def test_deck_save_persists_and_replies_layout(tmp_path):
    client, store = build_client(tmp_path, [])
    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps(hello(store.pair_token())))
        ws.receive_text()

        ws.send_text(
            json.dumps({"type": "deck.save", "id": "2", "payload": make_config()})
        )
        reply = json.loads(ws.receive_text())
        assert reply["type"] == "deck.layout"
        assert reply["payload"]["profiles"][0]["pages"][0]["buttons"][0]["id"] == "b-novo"

    assert store.load_config().find_button("b-novo") is not None


def test_deck_save_broadcasts_to_other_devices(tmp_path):
    client, store = build_client(tmp_path, [])
    token = store.pair_token()
    with client.websocket_connect("/ws") as ws_a, client.websocket_connect("/ws") as ws_b:
        ws_a.send_text(json.dumps(hello(token, "1")))
        ws_a.receive_text()
        ws_b.send_text(json.dumps(hello(token, "1")))
        ws_b.receive_text()

        ws_a.send_text(
            json.dumps({"type": "deck.save", "id": "2", "payload": make_config("Compartilhada")})
        )
        ws_a.receive_text()

        pushed = json.loads(ws_b.receive_text())
        assert pushed["type"] == "deck.layout"
        assert pushed["id"] == "broadcast"
        assert (
            pushed["payload"]["profiles"][0]["pages"][0]["buttons"][0]["label"]
            == "Compartilhada"
        )


def test_deck_save_invalid_returns_friendly_error(tmp_path):
    client, store = build_client(tmp_path, [])
    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps(hello(store.pair_token())))
        ws.receive_text()

        broken = make_config()
        del broken["profiles"][0]["pages"][0]["buttons"][0]["label"]
        ws.send_text(json.dumps({"type": "deck.save", "id": "3", "payload": broken}))
        reply = json.loads(ws.receive_text())
        assert reply["type"] == "error"
        assert "label" in reply["payload"]["message"]

    # config original intacta
    assert store.load_config().find_button("b-novo") is None


def _button(button_id, col=0):
    return Button(
        id=button_id,
        position=Position(col=col, row=0),
        label=button_id,
        action=OpenPathAction(path="~"),
    )


def test_config_rejects_duplicate_button_ids():
    with pytest.raises(ValidationError, match="duplicado"):
        DeckConfig(
            active_profile="a",
            profiles=[
                Profile(
                    id="a",
                    name="A",
                    pages=[
                        Page(id="p1", name="P", buttons=[_button("x"), _button("x", col=1)])
                    ],
                )
            ],
        )


def test_config_rejects_missing_active_profile():
    with pytest.raises(ValidationError, match="não existe"):
        DeckConfig(active_profile="fantasma", profiles=[Profile(id="a", name="A")])
