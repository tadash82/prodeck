"""Sistema de plugins: ações extras vindas de pacotes externos.

Qualquer pacote Python instalado pode registrar uma ação nova publicando um
entry point no grupo ``prodeck.actions`` que aponte para um ``ActionPlugin``:

    # no pyproject.toml do plugin
    [project.entry-points."prodeck.actions"]
    spotify = "prodeck_spotify:plugin"

O core não muda: o protocolo tem **um** tipo de ação ``plugin`` (ver
``PluginAction`` em models.py) que carrega ``name`` (qual plugin) e ``params``
(o que o usuário preencheu). O engine despacha para o plugin pelo ``name``; o
editor descobre os plugins e seus campos via ``GET /plugins``.
"""

from collections.abc import Callable
from dataclasses import dataclass
from importlib.metadata import entry_points

from loguru import logger

ENTRY_POINT_GROUP = "prodeck.actions"


@dataclass(frozen=True)
class PluginField:
    """Um campo que o usuário preenche no editor (vira chave em ``params``)."""

    key: str
    label: str
    placeholder: str = ""


@dataclass(frozen=True)
class ActionPlugin:
    """Uma ação de plugin: metadados pro editor + a função que executa.

    ``run`` recebe os ``params`` (dict de strings) e **levanta exceção** em
    falha — igual aos executores nativos (rodam em thread no engine).
    """

    name: str
    label: str
    icon: str
    run: Callable[[dict[str, str]], None]
    fields: tuple[PluginField, ...] = ()
    color: str = "#6366f1"


def load_plugins() -> dict[str, ActionPlugin]:
    """Descobre os plugins instalados (entry points), por ``name``.

    Tolerante a falhas: um plugin quebrado é ignorado com aviso no log, sem
    derrubar o agente nem os outros plugins.
    """
    found: dict[str, ActionPlugin] = {}
    for ep in entry_points(group=ENTRY_POINT_GROUP):
        try:
            obj = ep.load()
            plugin = obj if isinstance(obj, ActionPlugin) else obj()
            if not isinstance(plugin, ActionPlugin):
                logger.warning("plugin '{}' ignorado: não é um ActionPlugin", ep.name)
                continue
            found[plugin.name] = plugin
        except Exception as exc:  # import/entry point quebrado não derruba o resto
            logger.warning("plugin '{}' falhou ao carregar: {}", ep.name, exc)
    if found:
        logger.info("plugins carregados: {}", ", ".join(sorted(found)))
    return found


def plugins_metadata(plugins: dict[str, ActionPlugin]) -> list[dict]:
    """Metadados pro editor (``GET /plugins``): nome, rótulo, ícone e campos."""
    return [
        {
            "name": p.name,
            "label": p.label,
            "icon": p.icon,
            "color": p.color,
            "fields": [
                {"key": f.key, "label": f.label, "placeholder": f.placeholder}
                for f in p.fields
            ],
        }
        for p in plugins.values()
    ]


def plugin_executor(plugins: dict[str, ActionPlugin]) -> Callable[[object], None]:
    """Executor nativo do tipo ``plugin``: despacha pelo ``name`` da ação."""

    def execute(action) -> None:  # action: PluginAction
        plugin = plugins.get(action.name)
        if plugin is None:
            raise RuntimeError(f"plugin não encontrado: {action.name}")
        plugin.run(dict(action.params))

    return execute
