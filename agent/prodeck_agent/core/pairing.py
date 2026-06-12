"""Pareamento por token e registro de dispositivos conhecidos."""

import secrets
import shutil
import subprocess
from datetime import datetime, timezone

from loguru import logger

from .config import ConfigStore
from .models import Device


def _notify(title: str, body: str) -> None:
    """Notificação desktop best-effort (até o tray chegar na Fase 3)."""
    if shutil.which("notify-send"):
        subprocess.Popen(
            ["notify-send", "--app-name=ProDeck", title, body],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


class Pairing:
    def __init__(self, store: ConfigStore) -> None:
        self.store = store

    def verify(self, token: str) -> bool:
        return secrets.compare_digest(token, self.store.pair_token())

    def register(self, device_id: str, device_name: str) -> Device:
        """Registra (ou atualiza) um dispositivo que apresentou token válido."""
        devices = self.store.load_devices()
        now = datetime.now(timezone.utc)
        device = devices.devices.get(device_id)
        if device is None:
            device = Device(
                id=device_id, name=device_name, paired_at=now, last_seen=now
            )
            logger.info("novo dispositivo pareado: '{}' ({})", device_name, device_id)
            _notify("Dispositivo pareado", f"'{device_name}' agora controla este PC.")
        else:
            device.name = device_name
            device.last_seen = now
        devices.devices[device_id] = device
        self.store.save_devices(devices)
        return device
