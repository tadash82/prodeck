"""Entrypoint do agente: CLI, banner de pareamento e servidor."""

import argparse
import threading
from pathlib import Path

import qrcode
import uvicorn

from . import __version__, service
from .core.config import ConfigStore
from .core.engine import default_engine
from .core.net import all_lan_ips, lan_ip
from .core.pairing import Pairing
from .core.tls import ensure_certs
from .server.app import create_app, create_setup_app, pair_url
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
        print(f"    No PC, abra:  http://localhost:{http_port}/qr")
        print("    e siga os 2 passos com o celular (instalar certificado → abrir o app).\n")
        print(f"    app (HTTPS):  {pair_url(primary, https_port, token, 'https')}")
        print(f"    certificado:  {ca_path}")
    print(f"  config: {store.profiles_path} (edições à mão sincronizam sozinhas)\n")


def _serve_with_tls(
    main_app, setup_app, http_port: int, https_port: int, cert_path: Path, key_path: Path
) -> None:
    """App de setup em HTTP (thread, sem avisos) + app principal em HTTPS (thread
    principal). Em thread secundária o uvicorn não instala signal handlers, então
    Ctrl+C encerra o processo todo limpo pelo servidor HTTPS."""
    setup = uvicorn.Server(
        uvicorn.Config(setup_app, host="0.0.0.0", port=http_port, log_level="warning")
    )
    threading.Thread(target=setup.run, daemon=True).start()
    uvicorn.run(
        main_app,
        host="0.0.0.0",
        port=https_port,
        log_level="info",
        ssl_certfile=str(cert_path),
        ssl_keyfile=str(key_path),
    )


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
        "--install-service",
        action="store_true",
        help="instala e ativa o serviço systemd de usuário (autostart)",
    )
    parser.add_argument(
        "--uninstall-service", action="store_true", help="remove o serviço systemd"
    )
    args = parser.parse_args()

    if args.install_service:
        service.install(args.port)
        return
    if args.uninstall_service:
        service.uninstall()
        return

    store = ConfigStore()
    if args.reset_pairing:
        store.reset_pairing()
        print("Pareamento resetado: token novo gerado, dispositivos esquecidos.")

    if args.tls:
        cert_path, key_path, ca_path = ensure_certs(store.root, all_lan_ips())
        https_port = args.port + 1
        main_app = create_app(
            store, default_engine(), Pairing(store), args.port, https_port, ca_path
        )
        setup_app = create_setup_app(store, args.port, https_port, ca_path)
        _banner(store, args.port, https_port, ca_path)
        if not args.no_tray:
            start_tray(args.port)
        _serve_with_tls(main_app, setup_app, args.port, https_port, cert_path, key_path)
    else:
        app = create_app(store, default_engine(), Pairing(store), args.port)
        _banner(store, args.port, None, None)
        if not args.no_tray:
            start_tray(args.port)
        uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="info")


if __name__ == "__main__":
    main()
