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
│ open_app · open_path · open_url · hotkey · text · shell · macro │
│     (macro = sequência de passos com delays; shell é opt-in)    │
│                                                                 │
│  StateWatcher: estado dos botões (wpctl) a cada 2 s + push      │
│  pós-trigger + sync de edições à mão no profiles.json (mtime)   │
│  pystray (bandeja, best-effort) · loguru (log) · qrcode         │
└─────────────────────────────────────────────────────────────────┘
```

Decisão estrutural: **o agente serve a própria PWA**. Um único processo no PC entrega interface, pareamento e execução — não existe "instalar o app", existe "abrir o endereço".

## Estrutura do repositório (monorepo)

```
StreamDeck/
├── agent/                          # Python (uv)
│   ├── pyproject.toml
│   ├── tests/                      # pytest (modelos, config, engine, WS, file-sync)
│   └── prodeck_agent/
│       ├── main.py                 # CLI: --port, --reset-pairing, --(un)install-service, --no-tray
│       ├── tray.py                 # bandeja best-effort (pystray)
│       ├── service.py              # autostart: unit systemd de usuário
│       ├── gen_schema.py           # JSON Schema do protocolo (gera os tipos TS)
│       ├── server/
│       │   ├── app.py              # FastAPI, rotas HTTP, estáticos da PWA, lifespan do watcher
│       │   └── ws.py               # protocolo WS, ConnectionManager (broadcast)
│       ├── core/
│       │   ├── models.py           # Pydantic: config + protocolo — fonte única de verdade
│       │   ├── engine.py           # ActionEngine: registry, macros, gate do shell
│       │   ├── actions/            # open_app, open_path, open_url, hotkey, text, shell
│       │   ├── state.py            # StateWatcher: providers wpctl/pactl + sync do arquivo
│       │   ├── config.py           # ConfigStore: escrita atômica, backup, migração, default
│       │   ├── pairing.py          # token, devices.json, notificação de pareamento
│       │   └── net.py              # IPs de todas as interfaces
│       └── static/                 # build da PWA (vite build publica aqui)
├── app/                            # PWA (Vite + React + TS + Tailwind + Motion)
│   ├── tests/                      # vitest (deckOps)
│   └── src/
│       ├── components/             # DeckGrid, DeckButton, StatusBar, Toast, ConnectScreen
│       ├── components/edit/        # EditorSheet, MacroBuilder, IconPicker, ColorPicker, ManageSheet
│       ├── store/useDeck.ts        # Zustand: conexão, layout, edição, estados, toasts
│       ├── lib/                    # deckOps (operações puras), identity, useLongPress, keepAwake
│       ├── ws/client.ts            # reconexão com backoff, RTT, handshake
│       └── types/protocol.ts       # GERADO a partir do JSON Schema do Pydantic
├── scripts/
│   └── gen-types.sh                # Pydantic → JSON Schema → TypeScript
├── docs/
└── README.md
```

> O plano original previa `core/input/` com backends de teclado por plataforma;
> como o desenvolvimento está em X11, o pynput atende direto e a abstração só
> nasce quando o suporte a Wayland for implementado (YAGNI consciente).

## Modelo de dados

`~/.config/prodeck/profiles.json` — exemplo realista:

```json
{
  "version": 1,
  "active_profile": "dev",
  "allow_shell": false,
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

- **Ações são uma união discriminada** pelo campo `type` (Pydantic `Discriminator`) — tipos atuais: `open_app`, `open_path`, `open_url`, `hotkey`, `text`, `shell` e `macro` (passos das ações básicas + `delay`). Adicionar um tipo novo não quebra os existentes.
- `command` é **lista de argumentos** (nunca string única) → execução sem shell por padrão, sem injeção. A ação `shell` é a exceção explícita, atrás de `allow_shell` (padrão `false`) e sempre logada.
- Botões podem ter `"state": "mic_muted" | "audio_muted"` — o agente avalia o provider (wpctl/pactl) e envia `state.update` quando o fato muda no PC.
- `version` no topo + função de migração simples permitem evoluir o formato sem quebrar configs antigas; toda escrita é atômica e gera `.bak` da versão anterior.
- A PWA recebe esse modelo já resolvido via WS (`deck.layout`) — o celular não lê arquivo nenhum. O arquivo, porém, pode ser editado à mão no PC: o watcher detecta pelo mtime e propaga a todos os dispositivos.

## Protocolo WebSocket

Envelope único nos dois sentidos:

```json
{ "v": 1, "type": "action.trigger", "id": "uuid-curto", "payload": { } }
```

| Direção | `type` | Payload | Quando |
|---|---|---|---|
| C → S | `hello` | `{ token, device_id, device_name }` | Ao conectar |
| S → C | `hello.ok` | `{ agent_version, active_profile }` | Handshake aceito |
| S → C | `hello.denied` | `{ reason }` | Token inválido/revogado |
| C → S | `deck.get` | `{}` | Pedir layout atual |
| S → C | `deck.layout` | perfil completo (modelo acima) | Após `deck.get` ou mudança de config |
| C → S | `action.trigger` | `{ button_id }` | Toque no botão |
| S → C | `action.result` | `{ button_id, status: "ok"\|"error", message? }` | Resultado da execução (feedback visual) |
| C → S | `deck.save` | config completa | Edição pelo app/navegador; resposta é `deck.layout` |
| S → C | `state.update` | `{ button_id, active }` | Botões com estado (mute etc.): snapshot no `deck.get`, push pós-trigger e polling de 2 s |
| S → C | `error` | `{ message }` | Mensagem/config inválida — erros de validação resumidos de forma amigável |

Pushes sem requisição: além das respostas, o cliente recebe `deck.layout` com
`id: "broadcast"` (outro dispositivo salvou) ou `id: "file-sync"` (o
profiles.json mudou no disco), e `state.update` quando um fato do sistema muda.

- `id` correlaciona requisição/resposta; `v` permite evoluir o protocolo.
- Os modelos dessas mensagens vivem em `models.py` (Pydantic) e geram os tipos TS da PWA — **uma única fonte de verdade**.

## Fluxo de pareamento

```
1. Agente inicia → garante token persistente → imprime QR no terminal e na bandeja
   QR contém:  http://192.168.0.42:8710/?token=AbC123...
2. Celular escaneia → navegador abre a PWA (servida pelo próprio agente)
3. PWA conecta no WS e envia `hello` com o token da URL
4. Token válido → dispositivo entra em ~/.config/prodeck/devices.json e o PC
   mostra uma notificação ("'Pixel' agora controla este PC")
5. PWA guarda o token em localStorage → reconexões futuras são automáticas
6. Usuário faz "Adicionar à tela inicial" → vira app fullscreen com ícone
```

> Desvio consciente do plano original: a confirmação **bloqueante** no PC virou
> notificação informativa. Sem um tray interativo confiável no GNOME, um prompt
> travaria o pareamento; e quem apresenta o token provou ter acesso físico ao QR
> na tela do PC. Revogação: `--reset-pairing`. (ADR 7 abaixo.)

## Segurança

O agente **executa comandos no PC** — é o ponto mais sensível do projeto:

| Ameaça | Mitigação |
|---|---|
| Alguém na mesma rede dispara ações | Token obrigatório no handshake; sem token válido o WS é fechado |
| Token vazado | Tokens por dispositivo, revogáveis pela bandeja/config; regenerar invalida todos |
| Dispositivo novo silencioso | Notificação desktop no primeiro pareamento; revogação em lote com `--reset-pairing` |
| Injeção de comando | Ações executam `subprocess` **sem shell** e com lista de argumentos; a ação `shell` é opt-in (`allow_shell`, padrão off), com aviso no app e log de toda execução |
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
| 7 | Pareamento auto-aprova com token + notificação (sem prompt bloqueante) | Sem tray interativo confiável no GNOME; o token do QR já prova acesso físico ao PC | Tray/UI de confirmação chegar (Fase 4+) |
| 8 | Estado dos botões por polling (wpctl a cada 2 s) + push pós-trigger | Simples, sem dependências; eventos nativos do PipeWire são complexos | Precisar de latência sub-segundo ou de muitos providers |
| 9 | Sync de edições à mão por mtime no loop do watcher | Zero dependência extra (sem inotify/watchdog), 1 stat() a cada 2 s | Config crescer para múltiplos arquivos |
| 10 | `allow_shell` vive na própria config (editável pelo app) | Fricção consciente, não segurança real: `open_app` já executa binários arbitrários — o modelo de ameaça é o dispositivo pareado | Pareamento ganhar níveis de permissão |
