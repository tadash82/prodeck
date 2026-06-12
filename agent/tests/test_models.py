import pytest
from pydantic import ValidationError

from prodeck_agent.core.models import (
    CLIENT_MESSAGE,
    Button,
    DeckConfig,
    Grid,
    HelloMessage,
    OpenPathAction,
    Page,
    Position,
    Profile,
)


def make_config() -> DeckConfig:
    return DeckConfig(
        active_profile="dev",
        profiles=[
            Profile(
                id="dev",
                name="Dev",
                pages=[
                    Page(
                        id="p1",
                        name="Principal",
                        grid=Grid(cols=3, rows=4),
                        buttons=[
                            Button(
                                id="b1",
                                position=Position(col=0, row=0),
                                label="Home",
                                action=OpenPathAction(path="~"),
                            )
                        ],
                    )
                ],
            )
        ],
    )


def test_config_round_trip():
    config = make_config()
    assert DeckConfig.model_validate_json(config.model_dump_json()) == config


def test_action_discriminated_by_type():
    button = Button.model_validate(
        {
            "id": "b1",
            "position": {"col": 1, "row": 2},
            "label": "Pasta",
            "action": {"type": "open_path", "path": "~/Downloads"},
        }
    )
    assert isinstance(button.action, OpenPathAction)


def test_find_button():
    config = make_config()
    assert config.find_button("b1") is not None
    assert config.find_button("nope") is None


def test_client_message_parses_hello():
    msg = CLIENT_MESSAGE.validate_json(
        '{"type": "hello", "id": "1", "payload": {"token": "t", "device_id": "d"}}'
    )
    assert isinstance(msg, HelloMessage)
    assert msg.payload.device_name == "dispositivo"


def test_client_message_rejects_unknown_type():
    with pytest.raises(ValidationError):
        CLIENT_MESSAGE.validate_json('{"type": "hack", "id": "1"}')


def test_extra_fields_are_rejected():
    with pytest.raises(ValidationError):
        OpenPathAction.model_validate({"type": "open_path", "path": "~", "shell": True})
