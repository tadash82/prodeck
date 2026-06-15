"""Modelos da configuração e do protocolo — fonte única de verdade.

Os tipos TypeScript da PWA são gerados daqui via scripts/gen-types.sh;
mudou um modelo, rode o script para manter as duas pontas sincronizadas.
"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

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


class TextAction(StrictModel):
    type: Literal["text"] = "text"
    text: str = Field(min_length=1, max_length=5000)


class ShellAction(StrictModel):
    # roda no shell do sistema — só executa com allow_shell=true na config
    type: Literal["shell"] = "shell"
    command: str = Field(min_length=1)


class PluginAction(StrictModel):
    # ação fornecida por um plugin externo (entry point prodeck.actions);
    # `name` diz qual plugin e `params` são os campos que o usuário preencheu
    type: Literal["plugin"] = "plugin"
    name: str = Field(min_length=1)
    params: dict[str, str] = {}


class DelayStep(StrictModel):
    type: Literal["delay"] = "delay"
    ms: int = Field(ge=0, le=30_000)


MacroStep = Annotated[
    OpenAppAction
    | OpenPathAction
    | OpenUrlAction
    | HotkeyAction
    | TextAction
    | ShellAction
    | DelayStep,
    Field(discriminator="type"),
]


class MacroAction(StrictModel):
    type: Literal["macro"] = "macro"
    steps: list[MacroStep] = Field(min_length=1, max_length=50)


Action = Annotated[
    OpenAppAction
    | OpenPathAction
    | OpenUrlAction
    | HotkeyAction
    | TextAction
    | ShellAction
    | PluginAction
    | MacroAction,
    Field(discriminator="type"),
]


# ---------------------------------------------------------------- deck

class Position(StrictModel):
    col: int = Field(ge=0)
    row: int = Field(ge=0)


class Grid(StrictModel):
    cols: int = Field(default=3, ge=1, le=8)
    rows: int = Field(default=4, ge=1, le=10)


StateProvider = Literal["mic_muted", "audio_muted"]


class Button(StrictModel):
    id: str
    position: Position
    label: str
    icon: str = "mdi:gesture-tap-button"
    color: str = "#3b82f6"
    action: Action
    state: StateProvider | None = None


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
    allow_shell: bool = False

    @model_validator(mode="after")
    def _consistente(self) -> "DeckConfig":
        profile_ids = [p.id for p in self.profiles]
        if len(set(profile_ids)) != len(profile_ids):
            raise ValueError("há perfis com id duplicado")
        if self.profiles and self.active_profile not in profile_ids:
            raise ValueError(f"perfil ativo '{self.active_profile}' não existe")
        for profile in self.profiles:
            page_ids = [pg.id for pg in profile.pages]
            if len(set(page_ids)) != len(page_ids):
                raise ValueError(f"perfil '{profile.id}' tem páginas com id duplicado")
        button_ids = [
            b.id for p in self.profiles for pg in p.pages for b in pg.buttons
        ]
        if len(set(button_ids)) != len(button_ids):
            raise ValueError("há botões com id duplicado")
        return self

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


class ActionTestPayload(StrictModel):
    # ação avulsa pra experimentar no editor, sem precisar salvar um botão
    action: Action


class ActionTestMessage(StrictModel):
    v: int = PROTOCOL_VERSION
    type: Literal["action.test"] = "action.test"
    id: str
    payload: ActionTestPayload


class PingMessage(StrictModel):
    v: int = PROTOCOL_VERSION
    type: Literal["ping"] = "ping"
    id: str


class DeckSaveMessage(StrictModel):
    v: int = PROTOCOL_VERSION
    type: Literal["deck.save"] = "deck.save"
    id: str
    payload: "DeckConfig"


ClientMessage = Annotated[
    HelloMessage
    | DeckGetMessage
    | ActionTriggerMessage
    | ActionTestMessage
    | PingMessage
    | DeckSaveMessage,
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


class StateUpdatePayload(StrictModel):
    button_id: str
    active: bool


class StateUpdateMessage(StrictModel):
    v: int = PROTOCOL_VERSION
    type: Literal["state.update"] = "state.update"
    id: str
    payload: StateUpdatePayload


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
    | StateUpdateMessage
    | PongMessage
    | ErrorMessage,
    Field(discriminator="type"),
]
