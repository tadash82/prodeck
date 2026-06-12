"""Imprime o JSON Schema do protocolo e da config para gerar os tipos TS.

Uso: uv run python -m prodeck_agent.gen_schema  (ver scripts/gen-types.sh)
"""

import json

from pydantic import TypeAdapter

from .core import models

REF_TEMPLATE = "#/definitions/{model}"


def build_schema() -> dict:
    definitions: dict = {}

    def extract(schema: dict) -> dict:
        definitions.update(schema.pop("$defs", {}))
        return schema

    properties = {
        "client": extract(
            TypeAdapter(models.ClientMessage).json_schema(ref_template=REF_TEMPLATE)
        ),
        "server": extract(
            TypeAdapter(models.ServerMessage).json_schema(ref_template=REF_TEMPLATE)
        ),
        "config": extract(models.DeckConfig.model_json_schema(ref_template=REF_TEMPLATE)),
    }
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Protocol",
        "type": "object",
        "additionalProperties": False,
        "required": list(properties),
        "properties": properties,
        "definitions": definitions,
    }


if __name__ == "__main__":
    print(json.dumps(build_schema(), indent=2, ensure_ascii=False))
