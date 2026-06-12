"""Abre URL no navegador padrão."""

import webbrowser

from ..models import OpenUrlAction


def execute(action: OpenUrlAction) -> None:
    if not action.url.startswith(("http://", "https://")):
        raise RuntimeError(f"URL precisa começar com http:// ou https://: {action.url}")
    if not webbrowser.open(action.url):
        raise RuntimeError("nenhum navegador disponível")
