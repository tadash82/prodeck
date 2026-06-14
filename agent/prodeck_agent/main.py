"""Entrypoint do agente: CLI, banner de pareamento e servidor."""

import argparse
import asyncio
import os
import signal
import socket
import threading
import time
import webbrowser
from pathlib import Path

import qrcode
import uvicorn

from . import __version__, service
from .core.config import ConfigStore
from .core.engine import default_engine
from .core.net import all_lan_ips, lan_ip
from .core.pairing import Pairing
from .core.tls import ensure_certs
from .server.app import create_app, pair_url
from .tray import start_tray


def _banner(
    store: ConfigStore, http_port: int, https_port: int | None, ca_path: Path | None
) -> None:
    token = store.pair_token()
    primary = lan_ip()
    print(f"\n  ProDeck Agent v{__version__} — escaneie com o celular (mesma rede):\n")
    if https_port is None:
        qr = qrcode.QRCode(border=1)
        qr.add_data(pair_url(primary, http_port, token))
        qr.print_ascii(invert=True)
        for ip in all_lan_ips():
            marker = "→" if ip == primary else " "
            print(f"  {marker} {pair_url(ip, http_port, token)}")
        print(f"\n  QR de todas as interfaces: http://localhost:{http_port}/qr")
        print(f"  deck neste PC (navegador): {pair_url('localhost', http_port, token)}")
    else:
        print("  TLS ligado — onboarding por QR, sem digitar token nem topar avisos.\n")
        print(f"    parear (no PC):  http://localhost:{http_port}/qr  → 2 QRs p/ o celular")
        print(f"    configurar:      {pair_url('localhost', http_port, token)}")
        print("                     (deck no navegador do PC, sem aviso de certificado)")
        print(f"    app no celular:  {pair_url(primary, https_port, token, 'https')}  (tela cheia)")
        print(f"    certificado:     {ca_path}")
    print(f"  config: {store.profiles_path} (edições à mão sincronizam sozinhas)\n")


def _serve_with_tls(
    app, http_port: int, https_port: int, cert_path: Path, key_path: Path
) -> None:
    """Serve o MESMO app por dois listeners no MESMO event loop: HTTP (configurar
    pelo navegador do PC, sem avisos) e HTTPS (PWA em tela cheia no celular). Um
    único loop garante que o broadcast entre dispositivos funcione dos dois lados."""

    async def serve() -> None:
        servers = [
            uvicorn.Server(
                uvicorn.Config(app, host="0.0.0.0", port=http_port, log_level="info")
            ),
            uvicorn.Server(
                uvicorn.Config(
                    app,
                    host="0.0.0.0",
                    port=https_port,
                    log_level="info",
                    ssl_certfile=str(cert_path),
                    ssl_keyfile=str(key_path),
                )
            ),
        ]
        # Dois servers no mesmo loop: desliga os signal handlers internos e
        # instala um só que encerra ambos (senão um sobrescreve o do outro).
        for server in servers:
            server.install_signal_handlers = lambda: None

        def request_stop() -> None:
            for server in servers:
                server.should_exit = True

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, request_stop)
        await asyncio.gather(*(server.serve() for server in servers))

    asyncio.run(serve())


def _should_open_browser(no_open: bool) -> bool:
    """Abre o navegador só no uso interativo: nunca sob systemd nem headless."""
    if no_open or os.environ.get("INVOCATION_ID"):
        return False
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def _open_when_ready(url: str, port: int) -> None:
    """Espera o servidor responder na porta e abre o navegador (best-effort)."""

    def wait_and_open() -> None:
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            with socket.socket() as probe:
                probe.settimeout(0.3)
                if probe.connect_ex(("127.0.0.1", port)) == 0:
                    webbrowser.open(url)
                    return
            time.sleep(0.2)

    threading.Thread(target=wait_and_open, daemon=True).start()


def main() -> None:
    parser = argparse.ArgumentParser(prog="prodeck-agent")
    parser.add_argument("--port", type=int, default=8710)
    parser.add_argument(
        "--reset-pairing",
        action="store_true",
        help="gera token novo e esquece os dispositivos pareados",
    )
    parser.add_argument("--no-tray", action="store_true", help="não criar ícone na bandeja")
    parser.add_argument(
        "--tls",
        action="store_true",
        help="serve via HTTPS com certificado local (necessário p/ instalar a PWA em tela cheia)",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="não abrir a página de pareamento no navegador ao iniciar",
    )
    parser.add_argument(
        "--install-service",
        action="store_true",
        help="instala e ativa o serviço systemd de usuário (autostart)",
    )
    parser.add_argument(
        "--uninstall-service", action="store_true", help="remove o serviço systemd"
    )
    args = parser.parse_args()

    if args.install_service:
        service.install(args.port, args.tls)
        return
    if args.uninstall_service:
        service.uninstall()
        return

    store = ConfigStore()
    if args.reset_pairing:
        store.reset_pairing()
        print("Pareamento resetado: token novo gerado, dispositivos esquecidos.")

    if _should_open_browser(args.no_open):
        _open_when_ready(f"http://localhost:{args.port}/qr", args.port)

    if args.tls:
        cert_path, key_path, ca_path = ensure_certs(store.root, all_lan_ips())
        https_port = args.port + 1
        app = create_app(
            store, default_engine(), Pairing(store), args.port, https_port, ca_path
        )
        _banner(store, args.port, https_port, ca_path)
        if not args.no_tray:
            start_tray(args.port)
        _serve_with_tls(app, args.port, https_port, cert_path, key_path)
    else:
        app = create_app(store, default_engine(), Pairing(store), args.port)
        _banner(store, args.port, None, None)
        if not args.no_tray:
            start_tray(args.port)
        uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="info")


if __name__ == "__main__":
    main()
