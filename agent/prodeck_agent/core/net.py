"""Descoberta dos IPs locais da máquina."""

import socket
import subprocess


def lan_ip() -> str:
    """IP da interface com rota padrão (o connect em UDP não envia pacotes)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def all_lan_ips() -> list[str]:
    """Todos os IPv4 locais — necessário quando há mais de uma rede no caminho."""
    try:
        out = subprocess.run(
            ["ip", "-4", "-br", "addr"], capture_output=True, text=True, check=True
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return [lan_ip()]
    ips: list[str] = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] != "lo":
            ips += [p.split("/")[0] for p in parts[2:] if "." in p]
    return ips or [lan_ip()]
