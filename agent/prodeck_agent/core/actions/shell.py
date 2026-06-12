"""Comando de shell arbitrário — perigoso por natureza, por isso opt-in.

O engine só chama este executor quando allow_shell=true na config;
toda execução é registrada no log.
"""

import subprocess

from loguru import logger

from ..models import ShellAction


def execute(action: ShellAction) -> None:
    logger.warning("executando shell: {}", action.command)
    subprocess.Popen(
        action.command,
        shell=True,
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
