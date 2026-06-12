"""Execução de ações: registry de executores por tipo + sequências (macro).

Executores são funções síncronas que levantam exceção em falha;
o engine roda cada uma em thread para não travar o event loop do servidor.
"""

import asyncio
from collections.abc import Callable

from loguru import logger

from .models import Action, MacroStep

Executor = Callable[..., None]


class ActionEngine:
    def __init__(self) -> None:
        self._executors: dict[str, Executor] = {}

    def register(self, action_type: str, executor: Executor) -> None:
        self._executors[action_type] = executor

    async def run(self, action: Action, *, allow_shell: bool = False) -> tuple[bool, str]:
        if action.type == "macro":
            for index, step in enumerate(action.steps, 1):
                if step.type == "delay":
                    await asyncio.sleep(step.ms / 1000)
                    continue
                ok, detail = await self._run_one(step, allow_shell)
                if not ok:
                    return False, f"passo {index} ({step.type}): {detail}"
            return True, ""
        return await self._run_one(action, allow_shell)

    async def _run_one(
        self, action: Action | MacroStep, allow_shell: bool
    ) -> tuple[bool, str]:
        if action.type == "shell" and not allow_shell:
            return False, "ações shell estão desativadas — ative em Perfis e páginas"
        executor = self._executors.get(action.type)
        if executor is None:
            return False, f"nenhum executor para a ação '{action.type}'"
        try:
            await asyncio.to_thread(executor, action)
        except Exception as exc:
            logger.error("ação {} falhou: {}", action.type, exc)
            return False, str(exc)
        return True, ""


def default_engine() -> ActionEngine:
    from .actions import hotkey, open_app, open_path, open_url, shell, text

    engine = ActionEngine()
    engine.register("open_app", open_app.execute)
    engine.register("open_path", open_path.execute)
    engine.register("open_url", open_url.execute)
    engine.register("hotkey", hotkey.execute)
    engine.register("text", text.execute)
    engine.register("shell", shell.execute)
    return engine
