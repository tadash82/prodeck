"""Entrypoint do agente: CLI, banner de pareamento e servidor."""

import argparse
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


def _banner(store: ConfigStore, port: int, scheme: str, ca_path: Path | None) -> None:
    token = store.pair_token()
    primary = lan_ip()
    print(f"\n  ProDeck Agent v{__version__} — escaneie com o celular (mesma rede):\n")
    qr = qrcode.QRCode(border=1)
    qr.add_data(pair_url(primary, port, token, scheme))
    qr.print_ascii(invert=True)
    for ip in all_lan_ips():
        marker = "→" if ip == primary else " "
        print(f"  {marker} {pair_url(ip, port, token, scheme)}")
    print(f"\n  QR de todas as interfaces: {scheme}://localhost:{port}/qr")
    print(f"  deck neste PC (navegador): {pair_url('localhost', port, token, scheme)}")
    print(f"  config: {store.profiles_path} (edições à mão sincronizam sozinhas)")
    if ca_path is not None:
        print(
            "\n  TLS ligado. Para o celular confiar e instalar a PWA em tela cheia:\n"
            f"    1. abra {pair_url(primary, port, token, scheme)} e aceite o aviso de\n"
            '       certificado uma vez ("Avançado → prosseguir")\n'
            f"    2. instale o certificado raiz: {scheme}://{primary}:{port}/rootCA.pem\n"
            "       (Android: Configurações → Segurança → Instalar certificado → CA)\n"
            '    3. recarregue — vão surgir o cadeado e a opção "Instalar app"\n'
            f"    arquivo do certificado: {ca_path}"
        )
    print()


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

    scheme = "http"
    ssl_kwargs: dict[str, str] = {}
    ca_path: Path | None = None
    if args.tls:
        cert_path, key_path, ca_path = ensure_certs(store.root, all_lan_ips())
        scheme = "https"
        ssl_kwargs = {"ssl_certfile": str(cert_path), "ssl_keyfile": str(key_path)}

    app = create_app(store, default_engine(), Pairing(store), args.port, scheme, ca_path)
    _banner(store, args.port, scheme, ca_path)
    if not args.no_tray:
        start_tray(args.port)
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="info", **ssl_kwargs)


if __name__ == "__main__":
    main()
