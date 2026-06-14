"""Montagem do FastAPI: rotas HTTP, WebSocket e os estáticos da PWA."""

import asyncio
from contextlib import asynccontextmanager
from importlib.resources import files

import qrcode
import qrcode.image.svg
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .. import __version__
from ..core.config import ConfigStore
from ..core.engine import ActionEngine
from ..core.net import all_lan_ips
from ..core.pairing import Pairing
from ..core.state import StateWatcher
from .ws import ConnectionManager, deck_ws

# Resolve pelo loader do pacote (não por caminho relativo a __file__), para que
# a PWA seja servida tanto rodando do source quanto instalada via uv/pipx.
STATIC_DIR = files("prodeck_agent") / "static"


def pair_url(ip: str, port: int, token: str) -> str:
    return f"http://{ip}:{port}/?token={token}"


def create_app(
    store: ConfigStore, engine: ActionEngine, pairing: Pairing, port: int
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        poller = asyncio.create_task(app.state.watcher.run())
        yield
        poller.cancel()

    app = FastAPI(title="ProDeck Agent", version=__version__, lifespan=lifespan)
    app.state.store = store
    app.state.engine = engine
    app.state.pairing = pairing
    app.state.version = __version__
    app.state.connections = ConnectionManager()
    app.state.watcher = StateWatcher(store, app.state.connections)

    app.websocket("/ws")(deck_ws)

    @app.get("/qr")
    async def qr_page() -> HTMLResponse:
        """Um QR por interface de rede — escaneie o da rede em que o celular está."""
        token = store.pair_token()
        cards = []
        for ip in all_lan_ips():
            url = pair_url(ip, port, token)
            raw = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage).to_string()
            svg = (raw.decode() if isinstance(raw, bytes) else raw).split("?>", 1)[-1]
            cards.append(
                f"<figure>{svg}<figcaption>http://{ip}:{port}</figcaption></figure>"
            )
        html = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ProDeck · Parear dispositivo</title>
<style>
  body {{ background:#0b1220; color:#e2e8f0; font-family:system-ui,sans-serif;
         display:flex; flex-direction:column; gap:1.5rem; align-items:center;
         justify-content:center; min-height:100vh; margin:0; padding:2rem; }}
  h1 {{ font-size:1.1rem; font-weight:600; margin:0; }}
  p  {{ color:#94a3b8; font-size:.9rem; margin:0; text-align:center; }}
  .cards {{ display:flex; flex-wrap:wrap; gap:2rem; justify-content:center; }}
  figure {{ background:#fff; border-radius:16px; padding:18px; margin:0; text-align:center; }}
  svg {{ width:240px; height:240px; display:block; }}
  figcaption {{ color:#0f172a; font-family:ui-monospace,monospace; font-size:.9rem; margin-top:.6rem; }}
</style></head>
<body>
  <h1>Parear dispositivo</h1>
  <p>Escaneie com a câmera do celular o QR da rede em que ele está.<br>
     O endereço já leva o token de pareamento.</p>
  <div class="cards">{''.join(cards)}</div>
</body></html>"""
        return HTMLResponse(html)

    if STATIC_DIR.is_dir():
        app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="pwa")

    return app
