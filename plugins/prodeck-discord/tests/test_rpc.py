"""Testes do cliente RPC sem socket real: protocolo, cache e toggle."""

import threading

import prodeck_discord.rpc as rpc


def test_socket_candidates_cobre_nativo_flatpak_e_snap(monkeypatch):
    monkeypatch.setenv("XDG_RUNTIME_DIR", "/run/user/1000")
    paths = [str(p) for p in rpc._socket_candidates()]
    assert "/run/user/1000/discord-ipc-0" in paths
    assert any("app/com.discordapp.Discord/discord-ipc-0" in p for p in paths)
    assert any("snap.discord/discord-ipc-0" in p for p in paths)
    assert len(paths) == 30  # 3 raízes × 10 índices


def test_frame_header_round_trip():
    op, length = rpc._HEADER.unpack(rpc._HEADER.pack(rpc.OP_FRAME, 42))
    assert (op, length) == (rpc.OP_FRAME, 42)


def test_dispatch_atualiza_cache_e_resolve_nonce():
    client = rpc.DiscordRPC()
    event = threading.Event()
    slot: dict = {}
    client._pending["n1"] = (event, slot)
    client._dispatch(
        rpc.OP_FRAME,
        {"cmd": "DISPATCH", "evt": "VOICE_SETTINGS_UPDATE", "data": {"mute": True}},
    )
    assert client._voice["mute"] is True
    client._dispatch(
        rpc.OP_FRAME,
        {"cmd": "GET_VOICE_SETTINGS", "nonce": "n1", "data": {"deaf": True}},
    )
    assert event.is_set() and slot["data"] == {"deaf": True}


def test_dispatch_erro_vira_excecao_no_request():
    client = rpc.DiscordRPC()
    event = threading.Event()
    slot: dict = {}
    client._pending["n2"] = (event, slot)
    client._dispatch(
        rpc.OP_FRAME,
        {"evt": "ERROR", "nonce": "n2", "data": {"message": "token inválido"}},
    )
    assert slot["error"] == "token inválido"


def test_dispatch_ping_responde_pong(monkeypatch):
    client = rpc.DiscordRPC()
    sent = []
    monkeypatch.setattr(client, "_send", lambda op, obj: sent.append((op, obj)))
    client._dispatch(rpc.OP_PING, {"nonce": "p"})
    assert sent == [(rpc.OP_PONG, {"nonce": "p"})]


def test_toggle_le_estado_real_e_inverte(monkeypatch):
    client = rpc.DiscordRPC()
    client._up.set()
    calls = []

    def fake_request(cmd, args=None, timeout=8.0):
        calls.append((cmd, args))
        return {"mute": False, "deaf": False} if cmd == "GET_VOICE_SETTINGS" else {}

    monkeypatch.setattr(client, "_request", fake_request)
    assert client.toggle("mute") is True
    assert ("SET_VOICE_SETTINGS", {"mute": True}) in calls
    assert client._voice["mute"] is True


def test_toggle_sem_auth_pede_para_autorizar(monkeypatch):
    monkeypatch.setattr(rpc.auth, "load", lambda: None)
    client = rpc.DiscordRPC()  # _up nunca setado
    try:
        client.toggle("mute")
    except RuntimeError as exc:
        assert "autoriza" in str(exc).lower()
    else:  # pragma: no cover
        raise AssertionError("deveria ter levantado RuntimeError")


def test_toggle_autorizado_mas_offline_pede_abrir_discord(monkeypatch):
    monkeypatch.setattr(rpc.auth, "load", lambda: {"access_token": "x"})
    client = rpc.DiscordRPC()  # _up nunca setado
    try:
        client.toggle("mute")
    except RuntimeError as exc:
        assert "não conectado" in str(exc).lower()
    else:  # pragma: no cover
        raise AssertionError("deveria ter levantado RuntimeError")


def test_voice_state_none_quando_desconectado():
    client = rpc.DiscordRPC()
    assert client.voice_state() is None
    client._up.set()
    assert client.voice_state() == {"mute": False, "deaf": False}
