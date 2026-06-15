"""Contrato da camada de plataforma (providers por SO)."""

from prodeck_agent.core.platform import current
from prodeck_agent.core.platform.linux import LinuxPlatform
from prodeck_agent.core.platform.windows import WindowsPlatform

REQUIRED = ("presets", "installed_apps", "active_window", "is_muted", "starter_buttons")


def test_current_returns_provider_for_this_os():
    p = current()
    for method in REQUIRED:
        assert callable(getattr(p, method))


def test_linux_provider_shape():
    p = LinuxPlatform()
    assert p.name == "linux"
    # starter_buttons devolve dicts prontos pro default_config
    for b in p.starter_buttons():
        assert {"label", "icon", "color", "action"} <= b.keys()
        assert "type" in b["action"]
    # presets têm o formato que o editor espera
    for preset in p.presets():
        assert {"label", "icon", "color", "command", "state"} <= preset.keys()


def test_windows_provider_is_loadable_and_degrades():
    # carregável fora do Windows (ctypes só é usado em runtime, com try/except)
    p = WindowsPlatform()
    assert p.name == "windows"
    assert p.installed_apps() == []
    assert p.is_muted("source") is False
    assert p.active_window() is None  # sem windll no Linux → None, sem estourar
    assert all("command" in pr for pr in p.presets())
