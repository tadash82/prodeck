"""Modelos da configuração e do protocolo — fonte única de verdade.

Os tipos TypeScript da PWA são gerados daqui via scripts/gen-types.sh;
mudou um modelo, rode o script para manter as duas pontas sincronizadas.
"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

PROTOCOL_VERSION = 1
CONFIG_VERSION = 1


class StrictModel(BaseModel):
    # extra="forbid" gera additionalProperties:false no JSON Schema,
    # o que produz tipos TS fechados e rejeita payloads malformados
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------- ações

class OpenAppAction(StrictModel):
    type: Literal["open_app"] = "open_app"
    command: list[str] = Field(min_length=1)


class OpenPathAction(StrictModel):
    type: Literal["open_path"] = "open_path"
    path: str


class OpenUrlAction(StrictModel):
    type: Literal["open_url"] = "open_url"
    url: str


class HotkeyAction(StrictModel):
    type: Literal["hotkey"] = "hotkey"
    keys: list[str] = Field(min_length=1)


Action = Annotated[
    OpenAppAction | OpenPathAction | OpenUrlAction | HotkeyAction,
    Field(discriminator="type"),
]


# ---------------------------------------------------------------- deck

class Position(StrictModel):
    col: int = Field(ge=0)
    row: int = Field(ge=0)


class Grid(StrictModel):
    cols: int = Field(default=3, ge=1, le=8)
    rows: int = Field(default=4, ge=1, le=10)


class Button(StrictModel):
    id: str
    position: Position
    label: str
    icon: str = "mdi:gesture-tap-button"
    color: str = "#3b82f6"
    action: Action


class Page(StrictModel):
    id: str
    name: str
    grid: Grid = Grid()
    buttons: list[Button] = []


class Profile(StrictModel):
    id: str
    name: str
    pages: list[Page] = []


class DeckConfig(StrictModel):
    version: int = CONFIG_VERSION
    active_profile: str
    profiles: list[Profile] = []

    def find_button(self, button_id: str) -> Button | None:
        for profile in self.profiles:
            for page in profile.pages:
                for button in page.buttons:
                    if button.id == button_id:
                        return button
        return None


# ---------------------------------------------------------------- dispositivos pareados

class Device(StrictModel):
    id: str
    name: str
    paired_at: datetime
    last_seen: datetime


class DevicesFile(StrictModel):
    devices: dict[str, Device] = {}


# ---------------------------------------------------------------- protocolo: cliente → servidor

class HelloPayload(StrictModel):
    token: str
    device_id: str
    device_name: str = "dispositivo"


class HelloMessage(StrictModel):
    v: int = PROTOCOL_VERSION
    type: Literal["hello"] = "hello"
    id: str
    payload: HelloPayload


class DeckGetMessage(StrictModel):
    v: int = PROTOCOL_VERSION
    type: Literal["deck.get"] = "deck.get"
    id: str


class ActionTriggerPayload(StrictModel):
    button_id: str


class ActionTriggerMessage(StrictModel):
    v: int = PROTOCOL_VERSION
    type: Literal["action.trigger"] = "action.trigger"
    id: str
    payload: ActionTriggerPayload


class PingMessage(StrictModel):
    v: int = PROTOCOL_VERSION
    type: Literal["ping"] = "ping"
    id: str


ClientMessage = Annotated[
    HelloMessage | DeckGetMessage | ActionTriggerMessage | PingMessage,
    Field(discriminator="type"),
]

CLIENT_MESSAGE = TypeAdapter[ClientMessage](ClientMessage)


# ---------------------------------------------------------------- protocolo: servidor → cliente

class HelloOkPayload(StrictModel):
    agent_version: str
    active_profile: str


class HelloOkMessage(StrictModel):
    v: int = PROTOCOL_VERSION
    type: Literal["hello.ok"] = "hello.ok"
    id: str
    payload: HelloOkPayload


class HelloDeniedPayload(StrictModel):
    reason: str


class HelloDeniedMessage(StrictModel):
    v: int = PROTOCOL_VERSION
    type: Literal["hello.denied"] = "hello.denied"
    id: str
    payload: HelloDeniedPayload


class DeckLayoutMessage(StrictModel):
    v: int = PROTOCOL_VERSION
    type: Literal["deck.layout"] = "deck.layout"
    id: str
    payload: DeckConfig


class ActionResultPayload(StrictModel):
    button_id: str
    status: Literal["ok", "error"]
    message: str = ""


class ActionResultMessage(StrictModel):
    v: int = PROTOCOL_VERSION
    type: Literal["action.result"] = "action.result"
    id: str
    payload: ActionResultPayload


class PongMessage(StrictModel):
    v: int = PROTOCOL_VERSION
    type: Literal["pong"] = "pong"
    id: str


class ErrorPayload(StrictModel):
    message: str


class ErrorMessage(StrictModel):
    v: int = PROTOCOL_VERSION
    type: Literal["error"] = "error"
    id: str | None = None
    payload: ErrorPayload


ServerMessage = Annotated[
    HelloOkMessage
    | HelloDeniedMessage
    | DeckLayoutMessage
    | ActionResultMessage
    | PongMessage
    | ErrorMessage,
    Field(discriminator="type"),
]
