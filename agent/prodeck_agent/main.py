"""ProDeck — Fase 0 (spike): valida o tubo celular → PC.

Um único botão hard-coded, sem pareamento e sem config — isso chega na Fase 1.
Critério de aceite: tocar no celular abre o VSCode no PC.
"""

import json
import socket
import subprocess
from pathlib import Path

import qrcode
import qrcode.image.svg
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from loguru import logger

PORT = 8710

# Ação única do spike (a Fase 1 troca isto por profiles.json):
ACTION = ["code-insiders", str(Path.home() / "Projetos" / "StreamDeck")]

app = FastAPI(title="ProDeck Agent — spike Fase 0")
_static = Path(__file__).parent / "static"


def lan_ip() -> str:
    """IP desta máquina na rede local (o connect em UDP não envia pacote algum)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def all_lan_ips() -> list[str]:
    """Todos os IPv4 locais — útil quando há mais de uma rede no caminho."""
    try:
        out = subprocess.run(
            ["ip", "-4", "-br", "addr"], capture_output=True, text=True, check=True
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return []
    ips: list[str] = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] != "lo":
            ips += [p.split("/")[0] for p in parts[2:] if "." in p]
    return ips


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(_static / "index.html")


@app.get("/qr")
async def qr_page() -> HTMLResponse:
    """Um QR por interface de rede — escaneie o da rede em que o celular está."""
    cards = []
    for ip in all_lan_ips() or [lan_ip()]:
        url = f"http://{ip}:{PORT}"
        raw = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage).to_string()
        svg = (raw.decode() if isinstance(raw, bytes) else raw).split("?>", 1)[-1]
        cards.append(f'<figure>{svg}<figcaption>{url}</figcaption></figure>')
    html = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ProDeck · QR</title>
<style>
  body {{ background:#0b1220; color:#e2e8f0; font-family:system-ui,sans-serif;
         display:flex; flex-wrap:wrap; gap:2rem; align-items:center;
         justify-content:center; min-height:100vh; margin:0; padding:2rem; }}
  figure {{ background:#fff; border-radius:16px; padding:18px; margin:0; text-align:center; }}
  svg {{ width:240px; height:240px; display:block; }}
  figcaption {{ color:#0f172a; font-family:ui-monospace,monospace; font-size:.9rem; margin-top:.6rem; }}
</style></head>
<body>{''.join(cards)}</body></html>"""
    return HTMLResponse(html)


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    client = websocket.client.host if websocket.client else "?"
    logger.info("dispositivo conectado: {}", client)
    try:
        while True:
            msg = json.loads(await websocket.receive_text())
            reply: dict = {"id": msg.get("id")}
            match msg.get("type"):
                case "ping":
                    reply["type"] = "pong"
                case "action.trigger":
                    logger.info("executando: {}", " ".join(ACTION))
                    try:
                        subprocess.Popen(ACTION, start_new_session=True)
                        reply |= {"type": "action.result", "status": "ok"}
                    except OSError as exc:
                        logger.error("falha ao executar: {}", exc)
                        reply |= {
                            "type": "action.result",
                            "status": "error",
                            "message": str(exc),
                        }
                case unknown:
                    reply |= {"type": "error", "message": f"tipo desconhecido: {unknown}"}
            await websocket.send_text(json.dumps(reply))
    except WebSocketDisconnect:
        logger.info("dispositivo desconectado: {}", client)


def main() -> None:
    url = f"http://{lan_ip()}:{PORT}"
    qr = qrcode.QRCode(border=1)
    qr.add_data(url)
    print("\n  ProDeck · Fase 0 — escaneie com o celular (mesma rede Wi-Fi):\n")
    qr.print_ascii(invert=True)
    print(f"\n  {url}")
    for extra in (ip for ip in all_lan_ips() if ip != lan_ip()):
        print(f"  alternativa em outra interface: http://{extra}:{PORT}")
    print(f"\n  QR de todas as interfaces: http://localhost:{PORT}/qr\n")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")


if __name__ == "__main__":
    main()
