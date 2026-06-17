"""Autenticação OAuth2 com o Discord para o RPC local.

O escopo `rpc` (necessário para controlar mutar/ensurdecer) só é liberado para o
**dono** do app e até 50 testers — então cada usuário cria o próprio app no
Discord Developer Portal e autoriza uma vez. O fluxo:

    1. AUTHORIZE via IPC  → modal no Discord → `code`  (ver rpc.authorize)
    2. troca o `code` por access_token/refresh_token no endpoint OAuth2
    3. guarda tudo em ~/.config/prodeck/discord.json (chmod 600)

Daí o cliente RPC autentica com o access_token e o renova pelo refresh_token
quando expira, sem novo modal.
"""

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TOKEN_URL = "https://discord.com/api/oauth2/token"
# O Cloudflare do Discord rejeita o User-Agent padrão do urllib com 403 — a API
# exige um User-Agent identificável.
USER_AGENT = "ProDeck/0.1 (+https://github.com/tadash82/prodeck)"
# Precisa estar cadastrado em "Redirects" do app no Developer Portal. O fluxo é
# por IPC (sem navegador), mas o endpoint de token exige um redirect_uri válido.
REDIRECT_URI = "http://localhost"
SCOPES = ["rpc"]


def config_dir() -> Path:
    """Mesmo diretório do agente (~/.config/prodeck), respeitando o override."""
    override = os.environ.get("PRODECK_CONFIG_DIR")
    return Path(override) if override else Path.home() / ".config" / "prodeck"


def token_path() -> Path:
    return config_dir() / "discord.json"


def load() -> dict | None:
    """Credenciais salvas, ou None se a autorização nunca rodou."""
    path = token_path()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _save(creds: dict) -> None:
    path = token_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(creds, indent=2))
    os.chmod(tmp, 0o600)  # guarda client_secret e tokens — só o dono lê
    os.replace(tmp, path)


def _post_token(payload: dict) -> dict:
    body = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(
        TOKEN_URL,
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 (URL fixa)
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {exc.code} do Discord: {detail}") from exc


def _store_tokens(client_id: str, client_secret: str, data: dict) -> dict:
    if "access_token" not in data:
        raise RuntimeError(f"Discord não devolveu access_token: {data}")
    creds = {
        "client_id": client_id,
        "client_secret": client_secret,
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token", ""),
        # margem de 60s para nunca usar um token quase expirado
        "expires_at": time.time() + int(data.get("expires_in", 0)) - 60,
    }
    _save(creds)
    return creds


def exchange_code(client_id: str, client_secret: str, code: str) -> dict:
    """Troca o `code` do AUTHORIZE por tokens e persiste (usado no setup)."""
    data = _post_token(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        }
    )
    return _store_tokens(client_id, client_secret, data)


def refresh(creds: dict) -> dict:
    """Renova o access_token pelo refresh_token; persiste e retorna."""
    data = _post_token(
        {
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "grant_type": "refresh_token",
            "refresh_token": creds["refresh_token"],
        }
    )
    return _store_tokens(creds["client_id"], creds["client_secret"], data)


def valid_access_token() -> str | None:
    """access_token pronto para AUTHENTICATE, renovando se já expirou.

    Retorna None se não há credenciais salvas — o cliente trata como
    "não autenticado" e fica ocioso até a autorização rodar.
    """
    creds = load()
    if not creds or not creds.get("access_token"):
        return None
    if creds.get("refresh_token") and time.time() >= creds.get("expires_at", 0):
        creds = refresh(creds)
    return creds["access_token"]
