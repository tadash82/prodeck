"""Execução de ações: registry de executores por tipo.

Executores são funções síncronas que levantam exceção em falha;
o engine roda cada uma em thread para não travar o event loop do servidor.
"""

import asyncio
from collections.abc import Callable

from loguru import logger

from .models import Action

Executor = Callable[[Action], None]


class ActionEngine:
    def __init__(self) -> None:
        self._executors: dict[str, Executor] = {}

    def register(self, action_type: str, executor: Executor) -> None:
        self._executors[action_type] = executor

    async def run(self, action: Action) -> tuple[bool, str]:
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
    from .actions import hotkey, open_app, open_path, open_url

    engine = ActionEngine()
    engine.register("open_app", open_app.execute)
    engine.register("open_path", open_path.execute)
    engine.register("open_url", open_url.execute)
    engine.register("hotkey", hotkey.execute)
    return engine
