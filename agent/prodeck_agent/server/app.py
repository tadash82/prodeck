"""Montagem do FastAPI: rotas HTTP, WebSocket e os estáticos da PWA.

Com `--tls`, o mesmo app é servido por dois listeners no mesmo event loop (ver
`main._serve_with_tls`): HTTP na porta (configurar pelo navegador do PC, sem
avisos de certificado) e HTTPS na porta+1 (PWA em tela cheia no celular). A
página `/qr` mostra, por rede, o QR de instalar o certificado (HTTP) e o de
abrir o app (HTTPS).
"""

import asyncio
import secrets
from contextlib import asynccontextmanager
from importlib.resources import files
from pathlib import Path

import qrcode
import qrcode.image.svg
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .. import __version__
from ..core.apps import list_apps
from ..core.audio import audio_presets
from ..core.config import ConfigStore
from ..core.system import system_presets
from ..core.engine import ActionEngine
from ..core.net import all_lan_ips
from ..core.pairing import Pairing
from ..core.state import StateWatcher
from .ws import ConnectionManager, deck_ws

# Resolve pelo loader do pacote (não por caminho relativo a __file__), para que
# a PWA seja servida tanto rodando do source quanto instalada via uv/pipx.
STATIC_DIR = files("prodeck_agent") / "static"


def pair_url(ip: str, port: int, token: str, scheme: str = "http") -> str:
    return f"{scheme}://{ip}:{port}/?token={token}"


def _qr_svg(url: str) -> str:
    raw = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage).to_string()
    return (raw.decode() if isinstance(raw, bytes) else raw).split("?>", 1)[-1]


def _pairing_html(token: str, ips: list[str], http_port: int, https_port: int | None) -> str:
    """Página de pareamento. Sem TLS: um QR por rede. Com TLS: por rede, o QR de
    instalar o certificado (HTTP) e o de abrir o app (HTTPS)."""
    if https_port is None:
        blocks = "".join(
            f"<figure>{_qr_svg(pair_url(ip, http_port, token))}"
            f"<figcaption>http://{ip}:{http_port}</figcaption></figure>"
            for ip in ips
        )
        body = (
            "<h1>Parear dispositivo</h1>"
            "<p>Escaneie com a câmera do celular o QR da rede em que ele está — "
            "o endereço já leva o token, não precisa digitar nada.</p>"
            f'<div class="cards">{blocks}</div>'
        )
    else:
        nets = ""
        for ip in ips:
            cert_qr = _qr_svg(f"http://{ip}:{http_port}/rootCA.pem")
            app_qr = _qr_svg(pair_url(ip, https_port, token, "https"))
            nets += (
                f'<div class="net"><div class="net-h">rede {ip}</div><div class="cards">'
                f"<figure>{cert_qr}<figcaption>1 · instalar certificado</figcaption></figure>"
                f"<figure>{app_qr}<figcaption>2 · abrir o ProDeck</figcaption></figure>"
                "</div></div>"
            )
        body = (
            "<h1>Instalar no celular — 2 passos (só na 1ª vez)</h1>"
            "<p>Na rede em que o celular está: <b>1)</b> escaneie e instale o "
            "certificado (Android: Configurações → Segurança → Instalar certificado "
            "→ Certificado CA). <b>2)</b> escaneie para abrir o app e instalá-lo em "
            "tela cheia. Sem digitar token nem avisos de “conexão não segura”.</p>"
            f"{nets}"
        )
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ProDeck · Parear dispositivo</title>
<style>
  body {{ background:#0b1220; color:#e2e8f0; font-family:system-ui,sans-serif;
         display:flex; flex-direction:column; gap:1.5rem; align-items:center;
         justify-content:center; min-height:100vh; margin:0; padding:2rem; }}
  h1 {{ font-size:1.1rem; font-weight:600; margin:0; text-align:center; }}
  p  {{ color:#94a3b8; font-size:.9rem; margin:0; text-align:center; max-width:32rem; }}
  b  {{ color:#e2e8f0; }}
  .net {{ display:flex; flex-direction:column; gap:.8rem; align-items:center; }}
  .net-h {{ color:#64748b; font-family:ui-monospace,monospace; font-size:.8rem; }}
  .cards {{ display:flex; flex-wrap:wrap; gap:2rem; justify-content:center; }}
  figure {{ background:#fff; border-radius:16px; padding:18px; margin:0; text-align:center; }}
  svg {{ width:220px; height:220px; display:block; }}
  figcaption {{ color:#0f172a; font-family:ui-monospace,monospace; font-size:.85rem; margin-top:.6rem; }}
  .pc-row {{ display:flex; flex-direction:column; gap:.7rem; align-items:center;
            border-top:1px solid #1e293b; padding-top:1.5rem; width:100%; max-width:32rem; }}
  .pc-row span {{ color:#94a3b8; font-size:.9rem; text-align:center; }}
  .pc {{ display:inline-block; padding:.75rem 1.4rem; border-radius:12px; background:#2563eb;
        color:#fff; text-decoration:none; font-size:.95rem; font-weight:600; }}
  .pc:active {{ background:#1d4ed8; }}
</style></head>
<body>{body}
<div class="pc-row"><span>Vai configurar pelo próprio computador?</span>
<a class="pc" href="/?token={token}">Abrir o deck aqui</a></div>
</body></html>"""


def _add_qr_route(app: FastAPI, store: ConfigStore, http_port: int, https_port: int | None) -> None:
    @app.get("/qr")
    async def qr_page() -> HTMLResponse:
        return HTMLResponse(
            _pairing_html(store.pair_token(), all_lan_ips(), http_port, https_port)
        )


def _add_ca_route(app: FastAPI, ca_path: Path) -> None:
    @app.get("/rootCA.pem")
    async def root_ca() -> FileResponse:
        """Certificado raiz para instalar no celular e confiar no agente."""
        return FileResponse(
            ca_path, media_type="application/x-pem-file", filename="ProDeck-rootCA.pem"
        )


def create_app(
    store: ConfigStore,
    engine: ActionEngine,
    pairing: Pairing,
    http_port: int,
    https_port: int | None = None,
    ca_path: Path | None = None,
) -> FastAPI:
    """App principal: PWA + WebSocket + estado. Servido em HTTP (config pelo PC)
    e/ou HTTPS (PWA em tela cheia no celular) — ver main._serve_with_tls."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Com --tls o app é servido por dois listeners (HTTP + HTTPS) no mesmo
        # event loop, então o lifespan roda duas vezes: o watcher sobe só uma.
        if getattr(app.state, "poller", None) is None:
            app.state.poller = asyncio.create_task(app.state.watcher.run())
        yield
        poller = getattr(app.state, "poller", None)
        if poller is not None:
            poller.cancel()
            app.state.poller = None

    app = FastAPI(title="ProDeck Agent", version=__version__, lifespan=lifespan)
    app.state.store = store
    app.state.engine = engine
    app.state.pairing = pairing
    app.state.version = __version__
    app.state.connections = ConnectionManager()
    app.state.watcher = StateWatcher(store, app.state.connections)

    app.websocket("/ws")(deck_ws)
    _add_qr_route(app, store, http_port, https_port)
    if ca_path is not None:
        _add_ca_route(app, ca_path)

    @app.get("/apps")
    async def apps_list(token: str = "") -> JSONResponse:
        """Apps instalados (.desktop) para o seletor do editor — autenticado."""
        if not secrets.compare_digest(token, store.pair_token()):
            raise HTTPException(status_code=401)
        if not getattr(app.state, "apps_cache", None):
            app.state.apps_cache = await asyncio.to_thread(list_apps)
        return JSONResponse(app.state.apps_cache)

    @app.get("/presets")
    async def presets_list(token: str = "") -> JSONResponse:
        """Atalhos prontos (mídia + sistema) já com o comando certo da máquina."""
        if not secrets.compare_digest(token, store.pair_token()):
            raise HTTPException(status_code=401)
        return JSONResponse(audio_presets() + system_presets())

    if STATIC_DIR.is_dir():
        app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="pwa")

    return app
