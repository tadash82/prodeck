#!/usr/bin/env bash
# Gera um binário único do agente (Linux) via PyInstaller, com a PWA embutida.
# Pré-requisito: a PWA precisa estar buildada (cd app && npm run build) — o
# binário embute agent/prodeck_agent/static. Saída: agent/dist-bin/prodeck-agent
#
# O binário é dinâmico (glibc): roda em distros com glibc igual ou mais nova que
# a da máquina de build. Para máxima compatibilidade, builde numa distro antiga.
set -euo pipefail
cd "$(dirname "$0")/../agent"

if [ ! -f prodeck_agent/static/index.html ]; then
  echo "erro: PWA não buildada — rode 'cd app && npm run build' antes." >&2
  exit 1
fi

# Flags que importam:
# --collect-submodules prodeck_agent : pega os imports dinâmicos (actions,
#     platform.linux/windows, plugins.notify) que a análise estática não segue.
# --copy-metadata prodeck-agent      : leva o entry_points.txt, senão os PLUGINS
#     (load_plugins via importlib.metadata) somem no app congelado.
# --collect-data prodeck_agent       : embute a PWA (static/).
# --collect-all {pynput,Xlib,uvicorn,pystray}: backends de teclado/janela,
#     loop/protocolos do uvicorn e a bandeja (tudo com import dinâmico).
uv run --with pyinstaller pyinstaller \
  --noconfirm --clean --onefile \
  --name prodeck-agent \
  --distpath dist-bin \
  --collect-submodules prodeck_agent \
  --collect-data prodeck_agent \
  --copy-metadata prodeck-agent \
  --collect-all pynput \
  --collect-all Xlib \
  --collect-all uvicorn \
  --collect-all pystray \
  run.py

echo "ok: agent/dist-bin/prodeck-agent ($(du -h dist-bin/prodeck-agent | cut -f1))"
