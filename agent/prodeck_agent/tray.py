"""Ícone na bandeja do sistema — best-effort.

No GNOME a bandeja só existe com a extensão AppIndicator (padrão no Ubuntu)
e o pystray pode não ter backend utilizável; nesse caso o agente apenas
loga e segue rodando normalmente. O caminho garantido é o serviço systemd.
"""

import signal
import threading
import webbrowser

from loguru import logger


def start_tray(port: int) -> None:
    try:
        import pystray
        from PIL import Image, ImageDraw
    except Exception as exc:
        logger.info("bandeja indisponível ({}); seguindo sem ícone", exc)
        return

    def make_image() -> "Image.Image":
        image = Image.new("RGBA", (64, 64), (11, 18, 32, 255))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((8, 8, 30, 30), radius=6, fill=(59, 130, 246, 255))
        draw.rounded_rectangle((34, 8, 56, 30), radius=6, fill=(51, 65, 85, 255))
        draw.rounded_rectangle((8, 34, 30, 56), radius=6, fill=(51, 65, 85, 255))
        draw.rounded_rectangle((34, 34, 56, 56), radius=6, fill=(45, 212, 191, 255))
        return image

    def open_qr() -> None:
        webbrowser.open(f"http://localhost:{port}/qr")

    def quit_agent() -> None:
        icon.stop()
        signal.raise_signal(signal.SIGINT)

    icon = pystray.Icon(
        "prodeck",
        make_image(),
        "ProDeck Agent",
        menu=pystray.Menu(
            pystray.MenuItem("Parear dispositivo (QR)", open_qr),
            pystray.MenuItem("Sair", quit_agent),
        ),
    )

    def run() -> None:
        try:
            icon.run()
        except Exception as exc:
            logger.info("bandeja não pôde iniciar ({}); seguindo sem ícone", exc)

    threading.Thread(target=run, name="prodeck-tray", daemon=True).start()
