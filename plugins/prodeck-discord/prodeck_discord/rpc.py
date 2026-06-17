"""Cliente do RPC local do Discord sobre o socket IPC.

A integração precisa manter a conexão **aberta**: o Discord reverte o
mute/ensurdecer feito via RPC assim que o app que os alterou desconecta (doc
oficial — "settings reset ... after the controlling app disconnects"). Por isso
o cliente é um singleton de processo com uma thread supervisora que conecta,
autentica, assina `VOICE_SETTINGS_UPDATE` e reconecta sozinha, vivendo enquanto
o agente roda. Sem dependências externas: socket Unix + struct + json.

Protocolo: cada frame é `<opcode u32 LE><tamanho u32 LE><payload JSON>`. O
handshake (opcode 0) manda `{v, client_id}` e o Discord responde com o evento
`READY`; daí tudo vai por frames (opcode 1) correlacionados por `nonce`.
"""

import json
import os
import socket
import struct
import threading
import uuid
from pathlib import Path

from loguru import logger

from . import auth

OP_HANDSHAKE = 0
OP_FRAME = 1
OP_CLOSE = 2
OP_PING = 3
OP_PONG = 4

_HEADER = struct.Struct("<II")  # opcode + tamanho, little-endian


def _socket_candidates() -> list[Path]:
    """Caminhos possíveis do socket discord-ipc-{0..9} (nativo, Flatpak, Snap)."""
    base = os.environ.get("XDG_RUNTIME_DIR") or os.environ.get("TMPDIR") or "/tmp"
    roots = [
        base,
        os.path.join(base, "app", "com.discordapp.Discord"),  # Flatpak
        os.path.join(base, "snap.discord"),  # Snap
    ]
    return [Path(root) / f"discord-ipc-{i}" for root in roots for i in range(10)]


class DiscordRPC:
    """Conexão persistente e thread-safe com o cliente Discord local."""

    def __init__(self) -> None:
        self._sock: socket.socket | None = None
        self._write_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._pending: dict[str, tuple[threading.Event, dict]] = {}
        self._voice = {"mute": False, "deaf": False}
        self._ready = threading.Event()
        self._up = threading.Event()  # conectado + autenticado
        self._stop = threading.Event()
        self._supervisor: threading.Thread | None = None
        self._backoff = 1.0

    # ----------------------------------------------------------- ciclo de vida

    def start(self) -> None:
        if self._supervisor and self._supervisor.is_alive():
            return
        self._stop.clear()
        self._supervisor = threading.Thread(
            target=self._run, name="discord-rpc", daemon=True
        )
        self._supervisor.start()

    def stop(self) -> None:
        self._stop.set()
        self._close()

    # ------------------------------------------------------------ API pública

    def voice_state(self) -> dict | None:
        """{"mute": bool, "deaf": bool} se conectado+autenticado; senão None."""
        if not self._up.is_set():
            return None
        with self._state_lock:
            return dict(self._voice)

    def toggle(self, field: str) -> bool:
        """Inverte 'mute' ou 'deaf' no Discord. Retorna o novo valor."""
        if field not in ("mute", "deaf"):
            raise ValueError(f"campo inválido: {field}")
        if not self._up.wait(3.0):
            if auth.load() is None:
                raise RuntimeError(
                    "Discord ainda não autorizado. Rode 'prodeck-discord-auth' uma "
                    "vez (precisa de um app no Discord Developer Portal)."
                )
            raise RuntimeError(
                "Discord não conectado. Abra o Discord no PC e tente de novo."
            )
        # lê o estado real antes de inverter (não confia só no cache)
        current = self._request("GET_VOICE_SETTINGS")
        new_value = not bool(current.get(field, False))
        self._request("SET_VOICE_SETTINGS", {field: new_value})
        with self._state_lock:
            self._voice[field] = new_value
        return new_value

    # ------------------------------------------------------------- supervisor

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                token = auth.valid_access_token()
            except Exception as exc:
                logger.warning("discord: falha ao obter token: {}", exc)
                token = None
            if not token:
                self._stop.wait(5.0)  # sem credenciais: re-checa devagar
                continue
            try:
                self._connect_and_serve(token)
            except Exception as exc:
                logger.warning("discord rpc: {}", exc)
            finally:
                self._up.clear()
                self._ready.clear()
                self._close()
            if self._stop.is_set():
                break
            self._stop.wait(self._backoff)
            self._backoff = min(self._backoff * 2, 30.0)

    def _connect_and_serve(self, token: str) -> None:
        client_id = (auth.load() or {}).get("client_id", "")
        self._sock = self._open()
        self._send(OP_HANDSHAKE, {"v": 1, "client_id": client_id})
        reader = threading.Thread(
            target=self._read_loop, name="discord-rpc-rx", daemon=True
        )
        reader.start()
        if not self._ready.wait(10.0):
            raise RuntimeError("sem READY do Discord após o handshake")
        self._request("AUTHENTICATE", {"access_token": token})
        self._subscribe("VOICE_SETTINGS_UPDATE")
        initial = self._request("GET_VOICE_SETTINGS")
        with self._state_lock:
            self._voice["mute"] = bool(initial.get("mute", False))
            self._voice["deaf"] = bool(initial.get("deaf", False))
        self._backoff = 1.0
        self._up.set()
        logger.info("discord rpc: conectado e autenticado")
        reader.join()  # bloqueia até o socket cair → supervisor reconecta
        logger.info("discord rpc: conexão encerrada")

    # ------------------------------------------------------------ IO de baixo nível

    def _open(self) -> socket.socket:
        for path in _socket_candidates():
            if not path.exists():
                continue
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.connect(str(path))
                return sock
            except OSError:
                continue
        raise RuntimeError("socket do Discord não encontrado — o Discord está aberto?")

    def _send(self, op: int, obj: dict) -> None:
        data = json.dumps(obj).encode("utf-8")
        frame = _HEADER.pack(op, len(data)) + data
        with self._write_lock:
            if self._sock is None:
                raise RuntimeError("Discord desconectado")
            self._sock.sendall(frame)

    def _send_frame(self, obj: dict) -> None:
        self._send(OP_FRAME, obj)

    def _recv_exact(self, n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            assert self._sock is not None
            chunk = self._sock.recv(n - len(buf))
            if not chunk:
                return b""  # conexão fechada
            buf += chunk
        return buf

    def _read_loop(self) -> None:
        try:
            while not self._stop.is_set():
                header = self._recv_exact(_HEADER.size)
                if not header:
                    break
                op, length = _HEADER.unpack(header)
                body = self._recv_exact(length) if length else b""
                if length and not body:
                    break
                try:
                    payload = json.loads(body) if body else {}
                except json.JSONDecodeError:
                    continue
                self._dispatch(op, payload)
        except OSError:
            pass

    def _dispatch(self, op: int, payload: dict) -> None:
        if op == OP_PING:
            self._send(OP_PONG, payload)
            return
        evt = payload.get("evt")
        data = payload.get("data") or {}
        nonce = payload.get("nonce")
        # mantém o cache vivo: respostas de GET/SET e o evento VOICE_SETTINGS_UPDATE
        # trazem mute/deaf no topo de `data`
        if isinstance(data, dict) and ("mute" in data or "deaf" in data):
            with self._state_lock:
                if "mute" in data:
                    self._voice["mute"] = bool(data["mute"])
                if "deaf" in data:
                    self._voice["deaf"] = bool(data["deaf"])
        if evt == "READY":
            self._ready.set()
        if nonce and nonce in self._pending:
            event, slot = self._pending[nonce]
            if evt == "ERROR":
                slot["error"] = data.get("message", "erro do Discord")
            else:
                slot["data"] = data
            event.set()

    # ------------------------------------------------------------ requisições

    def _request(self, cmd: str, args: dict | None = None, timeout: float = 8.0) -> dict:
        nonce = str(uuid.uuid4())
        event = threading.Event()
        slot: dict = {}
        self._pending[nonce] = (event, slot)
        try:
            self._send_frame({"cmd": cmd, "args": args or {}, "nonce": nonce})
            if not event.wait(timeout):
                raise TimeoutError(f"Discord não respondeu a {cmd}")
            if "error" in slot:
                raise RuntimeError(f"{cmd}: {slot['error']}")
            return slot.get("data", {})
        finally:
            self._pending.pop(nonce, None)

    def _subscribe(self, event_name: str, timeout: float = 8.0) -> None:
        # SUBSCRIBE leva o evento no topo do envelope (não em args)
        nonce = str(uuid.uuid4())
        event = threading.Event()
        slot: dict = {}
        self._pending[nonce] = (event, slot)
        try:
            self._send_frame({"cmd": "SUBSCRIBE", "evt": event_name, "nonce": nonce})
            event.wait(timeout)  # melhor esforço: se falhar, seguimos com o cache
        finally:
            self._pending.pop(nonce, None)

    def _close(self) -> None:
        with self._write_lock:
            if self._sock is not None:
                try:
                    self._sock.close()
                except OSError:
                    pass
                self._sock = None


def authorize(client_id: str, scopes: list[str], timeout: float = 90.0) -> str:
    """Fluxo AUTHORIZE one-shot: abre o modal no Discord e devolve o `code`.

    Conexão dedicada (sem supervisor), usada só pela ferramenta de setup.
    """
    rpc = DiscordRPC()
    rpc._sock = rpc._open()
    rpc._send(OP_HANDSHAKE, {"v": 1, "client_id": client_id})
    reader = threading.Thread(target=rpc._read_loop, daemon=True)
    reader.start()
    try:
        if not rpc._ready.wait(10.0):
            raise RuntimeError("sem READY do Discord após o handshake")
        data = rpc._request(
            "AUTHORIZE", {"client_id": client_id, "scopes": scopes}, timeout=timeout
        )
        code = data.get("code")
        if not code:
            raise RuntimeError(f"AUTHORIZE não devolveu code: {data}")
        return code
    finally:
        rpc._stop.set()
        rpc._close()


# ----------------------------------------------------------------- singleton

_client: DiscordRPC | None = None
_client_lock = threading.Lock()


def client() -> DiscordRPC:
    """Cliente único do processo; inicia o supervisor na primeira chamada."""
    global _client
    with _client_lock:
        if _client is None:
            _client = DiscordRPC()
            _client.start()
        return _client


def voice_state() -> dict | None:
    """Estado de voz para o indicador 'aceso' do botão (consumido pelo agente)."""
    return client().voice_state()
