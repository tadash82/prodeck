"""Plugin de exemplo: dispara uma notificação de desktop (notify-send).

Mostra a anatomia mínima de um plugin do ProDeck: um ``ActionPlugin`` com os
campos que o editor renderiza e uma função ``run(params)`` que executa e levanta
exceção em falha. O entry point está no pyproject do agente:

    [project.entry-points."prodeck.actions"]
    notify = "prodeck_agent.plugins.notify:plugin"
"""

import shutil
import subprocess

from ..core.plugins import ActionPlugin, PluginField


def _run(params: dict[str, str]) -> None:
    if not shutil.which("notify-send"):
        raise RuntimeError("notify-send não encontrado — instale libnotify-bin")
    title = (params.get("title") or "ProDeck").strip()
    message = (params.get("message") or "").strip()
    subprocess.run(["notify-send", title, message], check=True)


plugin = ActionPlugin(
    name="notify",
    label="Notificação",
    icon="mdi:bell-outline",
    color="#6366f1",
    fields=(
        PluginField("title", "Título", "ProDeck"),
        PluginField("message", "Mensagem", "Olá do celular!"),
    ),
    run=_run,
)
