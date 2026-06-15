"""Instalação do agente como serviço systemd de usuário (autostart)."""

import subprocess
import sys
from pathlib import Path

UNIT_PATH = Path.home() / ".config/systemd/user/prodeck.service"

# Aspas em {python}: o caminho do interpretador pode conter espaços (ex.: um venv
# num drive "/media/.../Linux HD2/...") — sem aspas o systemd quebra o ExecStart.
UNIT_TEMPLATE = """[Unit]
Description=ProDeck Agent — deck de produtividade no celular
After=graphical-session.target

[Service]
ExecStart="{python}" -m prodeck_agent --no-tray{tls} --port {port}
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
"""


def install(port: int, tls: bool = False) -> None:
    UNIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    UNIT_PATH.write_text(
        UNIT_TEMPLATE.format(python=sys.executable, port=port, tls=" --tls" if tls else "")
    )
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", "--now", "prodeck.service"], check=True)
    print(f"Serviço instalado e iniciado ({UNIT_PATH}).")
    if tls:
        print(f"TLS ligado: setup em http://localhost:{port}/qr, app em HTTPS na {port + 1}.")
    print("Acompanhe com: journalctl --user -u prodeck -f")
    print("Obs.: para o atalho de teclado (hotkey) funcionar, a sessão gráfica")
    print("precisa expor DISPLAY ao systemd — padrão no Ubuntu/GNOME em X11.")


def uninstall() -> None:
    subprocess.run(
        ["systemctl", "--user", "disable", "--now", "prodeck.service"], check=False
    )
    UNIT_PATH.unlink(missing_ok=True)
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    print("Serviço removido.")
