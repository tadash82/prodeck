"""Persistência da configuração, dispositivos e token em ~/.config/prodeck."""

import json
import os
import secrets
import shutil
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, ValidationError

from .models import (
    CONFIG_VERSION,
    Button,
    DeckConfig,
    DevicesFile,
    Grid,
    HotkeyAction,
    OpenAppAction,
    OpenPathAction,
    OpenUrlAction,
    Page,
    Position,
    Profile,
)

DEFAULT_DIR = "~/.config/prodeck"


def _migrate(data: dict) -> dict:
    """Evolui configs antigas para o formato atual, versão a versão."""
    if data.get("version", 0) < 1:
        data["version"] = 1
    return data


def default_config() -> DeckConfig:
    """Perfil inicial com botões que funcionam nesta máquina."""
    buttons: list[Button] = []

    def add(label: str, icon: str, color: str, action) -> None:
        position = Position(col=len(buttons) % 3, row=len(buttons) // 3)
        buttons.append(
            Button(
                id=f"btn-{len(buttons) + 1}",
                position=position,
                label=label,
                icon=icon,
                color=color,
                action=action,
            )
        )

    editor = next(
        (e for e in ("code", "code-insiders", "cursor", "codium") if shutil.which(e)),
        None,
    )
    if editor:
        projeto = Path.home() / "Projetos"
        alvo = projeto if projeto.is_dir() else Path.home()
        add(
            "Editor",
            "mdi:microsoft-visual-studio-code",
            "#2dd4bf",
            OpenAppAction(command=[editor, str(alvo)]),
        )

    add("Downloads", "mdi:folder-download", "#f59e0b", OpenPathAction(path="~/Downloads"))
    add("Home", "mdi:folder-home", "#8b5cf6", OpenPathAction(path="~"))
    add("GitHub", "mdi:github", "#64748b", OpenUrlAction(url="https://github.com"))
    add("Terminal", "mdi:console", "#22c55e", HotkeyAction(keys=["ctrl", "alt", "t"]))
    add("Bloquear", "mdi:lock", "#ef4444", HotkeyAction(keys=["super", "l"]))

    return DeckConfig(
        version=CONFIG_VERSION,
        active_profile="padrao",
        profiles=[
            Profile(
                id="padrao",
                name="Principal",
                pages=[Page(id="p1", name="Página 1", grid=Grid(cols=3, rows=4), buttons=buttons)],
            )
        ],
    )


class ConfigStore:
    def __init__(self, root: Path | None = None) -> None:
        env_root = os.environ.get("PRODECK_CONFIG_DIR", DEFAULT_DIR)
        self.root = (root or Path(env_root)).expanduser()
        self.profiles_path = self.root / "profiles.json"
        self.devices_path = self.root / "devices.json"
        self.token_path = self.root / "secret.token"

    # ---------------------------------------------------------- profiles

    def load_config(self) -> DeckConfig:
        if not self.profiles_path.exists():
            config = default_config()
            self.save_config(config)
            logger.info("config inicial criada em {}", self.profiles_path)
            return config
        try:
            data = _migrate(json.loads(self.profiles_path.read_text(encoding="utf-8")))
            return DeckConfig.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise RuntimeError(
                f"config inválida em {self.profiles_path}: {exc}"
            ) from exc

    def save_config(self, config: DeckConfig) -> None:
        self._write_json(self.profiles_path, config)

    # ---------------------------------------------------------- devices

    def load_devices(self) -> DevicesFile:
        if not self.devices_path.exists():
            return DevicesFile()
        return DevicesFile.model_validate_json(
            self.devices_path.read_text(encoding="utf-8")
        )

    def save_devices(self, devices: DevicesFile) -> None:
        self._write_json(self.devices_path, devices)

    # ---------------------------------------------------------- token

    def pair_token(self) -> str:
        if self.token_path.exists():
            return self.token_path.read_text(encoding="utf-8").strip()
        token = secrets.token_urlsafe(24)
        self.root.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(token, encoding="utf-8")
        self.token_path.chmod(0o600)
        logger.info("novo token de pareamento gerado")
        return token

    def reset_pairing(self) -> None:
        """Gera token novo e esquece todos os dispositivos pareados."""
        self.token_path.unlink(missing_ok=True)
        self.devices_path.unlink(missing_ok=True)
        self.pair_token()

    # ---------------------------------------------------------- interno

    def _write_json(self, path: Path, data: BaseModel) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(data.model_dump_json(indent=2), encoding="utf-8")
        if path.exists():
            shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
        os.replace(tmp, path)
