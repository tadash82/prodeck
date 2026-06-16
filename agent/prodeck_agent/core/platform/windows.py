"""Provider de Windows — BEST-EFFORT, ainda NÃO validado em máquina Windows.

O que está implementado com APIs estáveis: janela ativa (Win32 via ctypes),
bloquear tela, terminal e print. O que falta (precisa de ferramenta/lib que não
quero assumir): estado de mute do áudio e lista de apps instalados — devolvem
vazio por ora, em vez de chutar comando errado.

TODO(windows): validar tudo numa sessão Windows real; áudio (CoreAudio/nircmd)
e apps (atalhos .lnk do Menu Iniciar) quando houver máquina para testar.
"""

import os
import shutil


def _active_window_win() -> tuple[str, str] | None:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    title = buf.value

    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    exe = ""
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if handle:
        size = wintypes.DWORD(260)
        name = ctypes.create_unicode_buffer(260)
        if kernel32.QueryFullProcessImageNameW(handle, 0, name, ctypes.byref(size)):
            exe = os.path.basename(name.value)
        kernel32.CloseHandle(handle)
    return (exe, title)


class WindowsPlatform:
    name = "windows"

    def presets(self) -> list[dict]:
        presets: list[dict] = [
            {
                "label": "Bloquear",
                "icon": "mdi:lock",
                "color": "#ef4444",
                "command": ["rundll32.exe", "user32.dll,LockWorkStation"],
                "state": None,
            }
        ]
        if shutil.which("snippingtool"):
            presets.append(
                {
                    "label": "Print",
                    "icon": "mdi:camera",
                    "color": "#8b5cf6",
                    "command": ["snippingtool.exe"],
                    "state": None,
                }
            )
        return presets  # áudio (mute/volume) ainda não — sem CLI nativa confiável

    def installed_apps(self) -> list[dict]:
        return []  # TODO(windows): varrer atalhos .lnk do Menu Iniciar

    def active_window(self) -> tuple[str, str] | None:
        try:
            return _active_window_win()
        except Exception:
            return None

    def focus_window(self, match: str) -> bool:
        return False  # TODO(windows): EnumWindows + SetForegroundWindow via ctypes

    def is_muted(self, kind: str) -> bool:
        return False  # TODO(windows): CoreAudio (sem dependência nova) ou nircmd

    def cpu_percent(self) -> float | None:
        return None  # TODO(windows): GetSystemTimes via ctypes

    def mem_info(self) -> tuple[float, float] | None:
        return None  # TODO(windows): GlobalMemoryStatusEx via ctypes

    def starter_buttons(self) -> list[dict]:
        term = "wt" if shutil.which("wt") else "cmd"
        return [
            {
                "label": "Terminal",
                "icon": "mdi:console",
                "color": "#22c55e",
                "action": {"type": "open_app", "command": [term]},
                "state": None,
            },
            {
                "label": "Bloquear",
                "icon": "mdi:lock",
                "color": "#ef4444",
                "action": {
                    "type": "open_app",
                    "command": ["rundll32.exe", "user32.dll,LockWorkStation"],
                },
                "state": None,
            },
        ]
