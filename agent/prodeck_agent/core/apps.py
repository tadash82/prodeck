"""Lista os aplicativos instalados (arquivos .desktop) para o seletor de apps
do editor de botões — devolve nome, comando e ícone (como data URL) de cada um,
para o usuário escolher "VS Code" em vez de digitar o comando e o ícone à mão.
"""

import base64
import configparser
import io
import os
import shlex
from pathlib import Path

from PIL import Image

_ICON_SIZE = 48
_FIELD_CODES = {"%f", "%u", "%d", "%n", "%i", "%c", "%k", "%v", "%m"}
_SIZES = ["scalable", "512x512", "256x256", "128x128", "96x96", "64x64", "48x48"]


def _app_dirs() -> list[Path]:
    """Diretórios XDG de aplicativos, com o do usuário em primeiro (prioridade)."""
    data_home = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local/share")
    data_dirs = os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share"
    seen: list[Path] = []
    for base in [data_home, *data_dirs.split(":")]:
        d = Path(base) / "applications"
        if d.is_dir() and d not in seen:
            seen.append(d)
    return seen


def _clean_exec(exec_str: str) -> list[str]:
    """Quebra o Exec do .desktop em argumentos, removendo os field codes (%U…)."""
    try:
        parts = shlex.split(exec_str)
    except ValueError:
        return []
    out = [p for p in parts if p.lower() not in _FIELD_CODES and not p.startswith("%")]
    return out


def _icon_path(name: str) -> Path | None:
    if not name:
        return None
    direct = Path(name)
    if direct.is_absolute():
        return direct if direct.is_file() else None
    roots = [
        Path.home() / ".local/share/icons",
        Path("/usr/share/icons"),
        Path("/usr/share/pixmaps"),
    ]
    for root in roots:
        if not root.is_dir():
            continue
        for ext in (".svg", ".png", ".xpm"):
            flat = root / f"{name}{ext}"
            if flat.is_file():
                return flat
        for theme in root.iterdir():
            if not theme.is_dir():
                continue
            for size in _SIZES:
                for ext in (".svg", ".png"):
                    cand = theme / size / "apps" / f"{name}{ext}"
                    if cand.is_file():
                        return cand
    return None


def _icon_data_url(path: Path) -> str | None:
    try:
        if path.suffix.lower() == ".svg":
            return "data:image/svg+xml;base64," + base64.b64encode(path.read_bytes()).decode()
        img = Image.open(path).convert("RGBA")
        img.thumbnail((_ICON_SIZE, _ICON_SIZE))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None


def _parse_desktop(path: Path) -> dict | None:
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        parser.read(path, encoding="utf-8")
    except (OSError, configparser.Error):
        return None
    if "Desktop Entry" not in parser:
        return None
    entry = parser["Desktop Entry"]
    if entry.get("Type") != "Application":
        return None
    if entry.get("NoDisplay", "false").lower() == "true":
        return None
    if entry.get("Hidden", "false").lower() == "true":
        return None
    name = entry.get("Name")
    command = _clean_exec(entry.get("Exec", ""))
    if not name or not command:
        return None
    return {"name": name, "exec": command, "icon_name": entry.get("Icon", "")}


def list_apps() -> list[dict]:
    """Aplicativos instalados, ordenados por nome, com o ícone como data URL."""
    by_id: dict[str, dict] = {}
    for directory in _app_dirs():
        for desktop in directory.glob("*.desktop"):
            if desktop.name in by_id:
                continue  # diretório do usuário (vem antes) tem prioridade
            entry = _parse_desktop(desktop)
            if entry:
                by_id[desktop.name] = entry
    apps = sorted(by_id.values(), key=lambda a: a["name"].lower())
    for app in apps:
        path = _icon_path(app.pop("icon_name", ""))
        app["icon"] = _icon_data_url(path) if path else None
    return apps
