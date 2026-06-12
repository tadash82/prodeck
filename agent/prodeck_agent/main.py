"""Entrypoint do agente: CLI, banner de pareamento e servidor."""

import argparse

import qrcode
import uvicorn

from . import __version__, service
from .core.config import ConfigStore
from .core.engine import default_engine
from .core.net import all_lan_ips, lan_ip
from .core.pairing import Pairing
from .server.app import create_app, pair_url
from .tray import start_tray


def _banner(store: ConfigStore, port: int) -> None:
    token = store.pair_token()
    primary = lan_ip()
    print(f"\n  ProDeck Agent v{__version__} — escaneie com o celular (mesma rede):\n")
    qr = qrcode.QRCode(border=1)
    qr.add_data(pair_url(primary, port, token))
    qr.print_ascii(invert=True)
    for ip in all_lan_ips():
        marker = "→" if ip == primary else " "
        print(f"  {marker} {pair_url(ip, port, token)}")
    print(f"\n  QR de todas as interfaces: http://localhost:{port}/qr")
    print(f"  config: {store.profiles_path}\n")


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

    app = create_app(store, default_engine(), Pairing(store), args.port)
    _banner(store, args.port)
    if not args.no_tray:
        start_tray(args.port)
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="info")


if __name__ == "__main__":
    main()
