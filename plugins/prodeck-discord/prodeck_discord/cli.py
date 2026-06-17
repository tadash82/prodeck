"""Ferramenta de setup: autoriza o ProDeck no seu app do Discord (uma vez).

Uso:
    prodeck-discord-auth
    PRODECK_DISCORD_CLIENT_ID=... PRODECK_DISCORD_CLIENT_SECRET=... prodeck-discord-auth

Pré-requisito: criar um app no Discord Developer Portal e cadastrar o redirect
``http://localhost`` (ver README). O Discord precisa estar aberto e logado.
"""

import os
import sys

from . import auth
from .rpc import authorize


def main() -> int:
    print("== ProDeck × Discord — autorização (uma vez) ==\n")
    client_id = (
        os.environ.get("PRODECK_DISCORD_CLIENT_ID") or input("Client ID: ").strip()
    )
    client_secret = (
        os.environ.get("PRODECK_DISCORD_CLIENT_SECRET")
        or input("Client Secret: ").strip()
    )
    if not client_id or not client_secret:
        print("erro: Client ID e Client Secret são obrigatórios.", file=sys.stderr)
        return 2

    print("\nAbrindo o modal no Discord — aprove o acesso na janela do Discord…")
    try:
        code = authorize(client_id, auth.SCOPES)
    except Exception as exc:
        print(f"erro ao autorizar via Discord: {exc}", file=sys.stderr)
        print("O Discord está aberto e logado neste PC?", file=sys.stderr)
        return 1

    try:
        auth.exchange_code(client_id, client_secret, code)
    except Exception as exc:
        print(f"erro ao trocar o code por token: {exc}", file=sys.stderr)
        print(
            "Você cadastrou o redirect 'http://localhost' no app do portal?",
            file=sys.stderr,
        )
        return 1

    print(f"\nok! token salvo em {auth.token_path()}")
    print("Adicione no editor os botões 'Discord: Mutar mic' / 'Discord: Ensurdecer'.")
    print("Reinicie o agente para carregar o plugin: systemctl --user restart prodeck")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
