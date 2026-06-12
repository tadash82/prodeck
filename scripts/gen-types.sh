#!/usr/bin/env bash
# Gera app/src/types/protocol.ts a partir dos modelos Pydantic do agente.
set -euo pipefail
cd "$(dirname "$0")/.."

uv run --project agent python -m prodeck_agent.gen_schema > /tmp/prodeck-schema.json
cd app
npx json2ts \
  --input /tmp/prodeck-schema.json \
  --output src/types/protocol.ts \
  --bannerComment "/* GERADO por scripts/gen-types.sh a partir dos modelos Pydantic — não editar à mão. */"
echo "ok: app/src/types/protocol.ts atualizado"
