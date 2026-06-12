"""Protocolo do deck sobre WebSocket: handshake por token, dispatch e broadcast."""

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
from pydantic import BaseModel, ValidationError

from ..core.models import (
    CLIENT_MESSAGE,
    ActionResultMessage,
    ActionResultPayload,
    ActionTriggerMessage,
    DeckGetMessage,
    DeckLayoutMessage,
    DeckSaveMessage,
    Device,
    ErrorMessage,
    ErrorPayload,
    HelloDeniedMessage,
    HelloDeniedPayload,
    HelloMessage,
    HelloOkMessage,
    HelloOkPayload,
    PingMessage,
    PongMessage,
)

AUTH_FAILED = 4401  # close code próprio: handshake recusado


class ConnectionManager:
    """Conexões autenticadas — alvo dos broadcasts de layout."""

    def __init__(self) -> None:
        self.active: set[WebSocket] = set()

    def add(self, websocket: WebSocket) -> None:
        self.active.add(websocket)

    def remove(self, websocket: WebSocket) -> None:
        self.active.discard(websocket)

    async def broadcast(
        self, message: BaseModel, exclude: WebSocket | None = None
    ) -> None:
        data = message.model_dump_json()
        for connection in list(self.active):
            if connection is exclude:
                continue
            try:
                await connection.send_text(data)
            except Exception:
                self.remove(connection)


def _friendly_validation_error(exc: ValidationError) -> str:
    """Resume os primeiros erros num texto que dá para mostrar no app."""
    parts = []
    for error in exc.errors()[:3]:
        loc = ".".join(str(piece) for piece in error["loc"])
        parts.append(f"{loc}: {error['msg']}" if loc else error["msg"])
    rest = exc.error_count() - len(parts)
    if rest > 0:
        parts.append(f"(+{rest} erros)")
    return "; ".join(parts)


async def deck_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    state = websocket.app.state
    client_host = websocket.client.host if websocket.client else "?"
    device: Device | None = None

    async def send(message: BaseModel) -> None:
        await websocket.send_text(message.model_dump_json())

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = CLIENT_MESSAGE.validate_json(raw)
            except ValidationError as exc:
                await send(
                    ErrorMessage(payload=ErrorPayload(message=_friendly_validation_error(exc)))
                )
                continue

            if isinstance(msg, HelloMessage):
                if not state.pairing.verify(msg.payload.token):
                    logger.warning("handshake recusado de {} (token inválido)", client_host)
                    await send(
                        HelloDeniedMessage(
                            id=msg.id, payload=HelloDeniedPayload(reason="invalid-token")
                        )
                    )
                    await websocket.close(code=AUTH_FAILED)
                    return
                device = state.pairing.register(
                    msg.payload.device_id, msg.payload.device_name
                )
                state.connections.add(websocket)
                logger.info("'{}' conectado ({})", device.name, client_host)
                await send(
                    HelloOkMessage(
                        id=msg.id,
                        payload=HelloOkPayload(
                            agent_version=state.version,
                            active_profile=state.store.load_config().active_profile,
                        ),
                    )
                )
                continue

            if device is None:
                await send(
                    HelloDeniedMessage(
                        id=msg.id, payload=HelloDeniedPayload(reason="not-authenticated")
                    )
                )
                await websocket.close(code=AUTH_FAILED)
                return

            if isinstance(msg, PingMessage):
                await send(PongMessage(id=msg.id))

            elif isinstance(msg, DeckGetMessage):
                await send(DeckLayoutMessage(id=msg.id, payload=state.store.load_config()))

            elif isinstance(msg, DeckSaveMessage):
                state.store.save_config(msg.payload)
                logger.info("'{}' salvou a configuração do deck", device.name)
                await send(DeckLayoutMessage(id=msg.id, payload=msg.payload))
                await state.connections.broadcast(
                    DeckLayoutMessage(id="broadcast", payload=msg.payload),
                    exclude=websocket,
                )

            elif isinstance(msg, ActionTriggerMessage):
                button_id = msg.payload.button_id
                button = state.store.load_config().find_button(button_id)
                if button is None:
                    ok, detail = False, f"botão não encontrado: {button_id}"
                else:
                    ok, detail = await state.engine.run(button.action)
                    logger.info(
                        "'{}' acionou [{}] {} → {}",
                        device.name,
                        button.action.type,
                        button.label,
                        "ok" if ok else f"erro: {detail}",
                    )
                await send(
                    ActionResultMessage(
                        id=msg.id,
                        payload=ActionResultPayload(
                            button_id=button_id,
                            status="ok" if ok else "error",
                            message=detail,
                        ),
                    )
                )
    except WebSocketDisconnect:
        if device is not None:
            logger.info("'{}' desconectado", device.name)
    finally:
        state.connections.remove(websocket)
