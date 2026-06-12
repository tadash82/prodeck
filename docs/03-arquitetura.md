# 03 — Arquitetura

## Visão geral

```
┌──────────────────── Celular (navegador/PWA) ────────────────────┐
│                                                                 │
│  ┌─────────────┐   ┌──────────────────┐   ┌──────────────────┐  │
│  │  Deck Grid  │   │ Editor de Botões │   │ Tela de Conexão  │  │
│  │ (uso diário)│   │     (Fase 2)     │   │ (QR/token/status)│  │
│  └──────┬──────┘   └────────┬─────────┘   └────────┬─────────┘  │
│         └───────────────────┴──────────────────────┘            │
│                    Zustand store + cliente WS                   │
└────────────────────────────┬────────────────────────────────────┘
                             │  WebSocket · JSON · Wi-Fi (LAN)
┌────────────────────────────▼────────────────────────────────────┐
│                     Agente no PC (Python)                       │
│                                                                 │
│  FastAPI/Uvicorn                                                │
│  ├── GET /            → serve a PWA (build estático embutido)   │
│  ├── GET /qr          → página/imagem do QR de pareamento       │
│  └── WS  /ws          → protocolo do deck                       │
│                                                                 │
│  ┌────────────┐  ┌───────────────┐  ┌───────────────────────┐   │
│  │  Pairing   │  │ Config Store  │  │     Action Engine     │   │
│  │ tokens/    │  │ profiles.json │  │  registry de          │   │
│  │ devices    │  │ (Pydantic)    │  │  executores           │   │
│  └────────────┘  └───────────────┘  └───────────┬───────────┘   │
│                                                 │               │
│         ┌────────────┬──────────────┬───────────┼─────────────┐ │
│         ▼            ▼              ▼           ▼             ▼ │
│     open_app     open_path      open_url     hotkey        shell│
│    (subprocess) (xdg-open)    (navegador)   (pynput)   (Fase 3) │
│                                                                 │
│  pystray (bandeja) · loguru (log de ações) · qrcode             │
└─────────────────────────────────────────────────────────────────┘
```

Decisão estrutural: **o agente serve a própria PWA**. Um único processo no PC entrega interface, pareamento e execução — não existe "instalar o app", existe "abrir o endereço".

## Estrutura do repositório (monorepo)

```
StreamDeck/
├── agent/                          # Python (uv)
│   ├── pyproject.toml
│   └── prodeck_agent/
│       ├── main.py                 # entrypoint: uvicorn + tray + QR
│       ├── server/
│       │   ├── app.py              # FastAPI, rotas HTTP, estáticos da PWA
│       │   └── ws.py               # handler WebSocket, dispatch de mensagens
│       ├── core/
│       │   ├── models.py           # Pydantic: Profile, Page, Button, Action, mensagens
│       │   ├── engine.py           # ActionRegistry + execução assíncrona
│       │   ├── actions/            # um módulo por tipo de ação
│       │   │   ├── open_app.py
│       │   │   ├── open_path.py
│       │   │   ├── open_url.py
│       │   │   ├── hotkey.py
│       │   │   └── macro.py        # Fase 3
│       │   ├── input/              # backends de teclado (x11.py, wayland.py, win.py)
│       │   ├── config.py           # load/save/migração de profiles.json
│       │   └── pairing.py          # tokens, dispositivos, QR
│       └── tray.py
├── app/                            # PWA (Vite + React + TS)
│   ├── package.json
│   └── src/
│       ├── components/             # DeckGrid, DeckButton, ConnectScreen, Editor/
│       ├── store/                  # Zustand: conexão, layout, perfil ativo
│       ├── ws/                     # cliente WS: reconexão, fila, handshake
│       └── types/protocol.ts       # GERADO a partir do JSON Schema do Pydantic
├── scripts/
│   └── gen-types.sh                # Pydantic → JSON Schema → TypeScript
├── docs/
└── README.md
```

## Modelo de dados

`~/.config/prodeck/profiles.json` — exemplo realista:

```json
{
  "version": 1,
  "active_profile": "dev",
  "profiles": [
    {
      "id": "dev",
      "name": "Desenvolvimento",
      "pages": [
        {
          "id": "main",
          "name": "Principal",
          "grid": { "cols": 4, "rows": 5 },
          "buttons": [
            {
              "id": "b1",
              "position": [0, 0],
              "label": "StreamDeck",
              "icon": "mdi:microsoft-visual-studio-code",
              "color": "#2dd4bf",
              "action": { "type": "open_app", "command": ["code", "/home/tadashi/Projetos/StreamDeck"] }
            },
            {
              "id": "b2",
              "position": [1, 0],
              "label": "Downloads",
              "icon": "mdi:folder-download",
              "color": "#f59e0b",
              "action": { "type": "open_path", "path": "~/Downloads" }
            },
            {
              "id": "b3",
              "position": [2, 0],
              "label": "Mutar Mic",
              "icon": "mdi:microphone-off",
              "color": "#ef4444",
              "action": { "type": "hotkey", "keys": ["ctrl", "shift", "m"] }
            },
            {
              "id": "b4",
              "position": [0, 1],
              "label": "Modo Trabalho",
              "icon": "mdi:rocket-launch",
              "color": "#8b5cf6",
              "action": {
                "type": "macro",
                "steps": [
                  { "type": "open_app", "command": ["code", "~/Projetos/StreamDeck"] },
                  { "type": "delay", "ms": 800 },
                  { "type": "open_url", "url": "https://github.com" },
                  { "type": "open_app", "command": ["gnome-terminal"] }
                ]
              }
            }
          ]
        }
      ]
    }
  ]
}
```

Regras:

- **Ações são uma união discriminada** pelo campo `type` (Pydantic `Discriminator`) — adicionar um tipo novo de ação não quebra os existentes.
- `command` é **lista de argumentos** (nunca string única) → execução sem shell por padrão, sem injeção.
- `version` no topo + função de migração simples permitem evoluir o formato sem quebrar configs antigas.
- A PWA recebe esse modelo já resolvido via WS (`deck.layout`) — o celular não lê arquivo nenhum.

## Protocolo WebSocket

Envelope único nos dois sentidos:

```json
{ "v": 1, "type": "action.trigger", "id": "uuid-curto", "payload": { } }
```

| Direção | `type` | Payload | Quando |
|---|---|---|---|
| C → S | `hello` | `{ token, device_name, app_version }` | Ao conectar |
| S → C | `hello.ok` | `{ agent_version, active_profile }` | Handshake aceito |
| S → C | `hello.denied` | `{ reason }` | Token inválido/revogado |
| C → S | `deck.get` | `{}` | Pedir layout atual |
| S → C | `deck.layout` | perfil completo (modelo acima) | Após `deck.get` ou mudança de config |
| C → S | `action.trigger` | `{ button_id }` | Toque no botão |
| S → C | `action.result` | `{ button_id, status: "ok"\|"error", message? }` | Resultado da execução (feedback visual) |
| C → S | `deck.save` | perfil editado | Fase 2 (editor) |
| S → C | `state.update` | `{ button_id, state }` | Fase 3 (botões toggle/dinâmicos) |

- `id` correlaciona requisição/resposta; `v` permite evoluir o protocolo.
- Os modelos dessas mensagens vivem em `models.py` (Pydantic) e geram os tipos TS da PWA — **uma única fonte de verdade**.

## Fluxo de pareamento

```
1. Agente inicia → garante token persistente → imprime QR no terminal e na bandeja
   QR contém:  http://192.168.0.42:8710/?token=AbC123...
2. Celular escaneia → navegador abre a PWA (servida pelo próprio agente)
3. PWA conecta no WS e envia `hello` com o token da URL
4. Primeira vez: agente exibe confirmação no PC ("Permitir 'Pixel do Alberto'?")
   → dispositivo entra na lista de pareados (~/.config/prodeck/devices.json)
5. PWA guarda o token em localStorage → reconexões futuras são automáticas
6. Usuário faz "Adicionar à tela inicial" → vira app fullscreen com ícone
```

## Segurança

O agente **executa comandos no PC** — é o ponto mais sensível do projeto:

| Ameaça | Mitigação |
|---|---|
| Alguém na mesma rede dispara ações | Token obrigatório no handshake; sem token válido o WS é fechado |
| Token vazado | Tokens por dispositivo, revogáveis pela bandeja/config; regenerar invalida todos |
| Dispositivo novo silencioso | Confirmação manual no PC no primeiro pareamento |
| Injeção de comando | Ações executam `subprocess` **sem shell** e com lista de argumentos; a ação `shell` (Fase 3) é opt-in, marcada como perigosa e logada |
| Exposição fora da LAN | Bind padrão na interface local; documentação explícita: **nunca** expor a porta na internet; rate limit por conexão |
| Auditoria | loguru registra cada ação executada com origem (dispositivo) e timestamp |

TLS local (mkcert) entra na Fase 4 como opcional — ver nota sobre HTTPS no doc 02.

## Decisões registradas (mini-ADRs)

| # | Decisão | Motivo | Revisitar se… |
|---|---|---|---|
| 1 | PWA servida pelo agente, não app de loja | Fricção zero, atualização junto do agente | Precisar de recurso nativo (widget, NFC) → Flutter (Fase 5) |
| 2 | WebSocket JSON, não REST/MQTT | Push de estado + simplicidade | Nunca, provavelmente |
| 3 | Config em JSON único, não SQLite | Legível, versionável, backup trivial | Perfis ficarem enormes ou precisar de histórico |
| 4 | Tipos TS gerados do Pydantic | Protocolo com fonte única de verdade | — |
| 5 | `command` como lista, execução sem shell | Segurança por padrão | — |
| 6 | Monorepo `agent/` + `app/` | Projeto pequeno, protocolo compartilhado | Times/repos separados um dia |
