# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

ProDeck transforma o celular num "Stream Deck" touch que controla o PC pela LAN. Monorepo com dois pacotes: `agent/` (Python/FastAPI que roda no PC e executa as ações) e `app/` (PWA React que roda no celular/navegador). O agente **serve a própria PWA** — não há app de loja, o build do front sai dentro do pacote Python.

## Comandos

```bash
# Rodar o agente (imprime QR + URLs de pareamento no terminal)
cd agent && uv run prodeck-agent            # use --no-tray, --reset-pairing, --port N, --tls
uv run prodeck-agent --install-service      # autostart via systemd de usuário

# Testes
cd agent && uv run pytest                    # tudo
cd agent && uv run pytest tests/test_ws.py::test_hello_with_valid_token   # um teste
cd app && npm test                           # vitest (deckOps)

# Desenvolvimento da PWA (proxy /ws e /qr → agente na 8710; rode o agente junto)
cd app && npm run dev
cd app && npm run build      # tsc --noEmit + vite build → publica em agent/prodeck_agent/static/
```

## Fonte única de verdade: Pydantic → TypeScript

O protocolo WebSocket e o modelo de configuração vivem **só** em `agent/prodeck_agent/core/models.py` (Pydantic). Os tipos do front (`app/src/types/protocol.ts`) são **gerados**, nunca editados à mão.

**Mudou qualquer modelo em `models.py`? Rode `scripts/gen-types.sh`** (Pydantic → JSON Schema via `gen_schema.py` → `json2ts`). Esquecer isso faz o front e o agente divergirem silenciosamente. Os modelos usam `extra="forbid"` (`StrictModel`) para gerar tipos TS fechados e rejeitar payloads malformados.

## Arquitetura

**Protocolo WS** (`server/ws.py`): envelope único `{ v, type, id, payload }` nos dois sentidos; `id` correlaciona requisição/resposta. Toda conexão começa com `hello` (token); sem handshake válido o socket é fechado com code 4401. Mensagens principais: `deck.get`/`deck.layout` (layout), `action.trigger`/`action.result` (executar botão), `deck.save` (editar config), `state.update` (estado ao vivo), `ping`/`pong` (RTT). O `ConnectionManager` faz broadcast: ao salvar, os **outros** dispositivos recebem `deck.layout` com `id: "broadcast"`.

**Ações como união discriminada** (`core/models.py`, `core/engine.py`): cada `Action` é discriminada por `type` (`open_app`, `open_path`, `open_url`, `hotkey`, `text`, `shell`, `macro`). `macro` é uma lista de passos (ações básicas + `delay`). Adicionar um tipo novo = nova classe Pydantic na união + executor registrado em `default_engine()`. Executores são funções **síncronas** que levantam exceção em falha; o engine roda cada uma em `asyncio.to_thread` para não travar o event loop.

**Segurança do `command`**: `command` é sempre **lista de argumentos** → `subprocess` sem shell, sem injeção. A ação `shell` (string única, roda no shell) é a exceção, barrada por `allow_shell` na config (padrão `false`) e checada no engine antes de executar. `allow_shell` é editável pelo próprio app — é fricção consciente, não barreira de segurança (`open_app` já roda binários arbitrários; o modelo de ameaça é o dispositivo pareado, ver ADR 10 em `docs/03-arquitetura.md`).

**ConfigStore** (`core/config.py`): persiste `profiles.json`, `devices.json` e `secret.token` em `~/.config/prodeck` (override via env `PRODECK_CONFIG_DIR`). Escrita é atômica (`tmp` + `os.replace`) e gera `.bak`. Há `_migrate()` versionado (`version` no topo do JSON) para evoluir o formato sem quebrar configs antigas. `default_config()` detecta binários da máquina (`shutil.which`) para montar botões que de fato funcionam.

**StateWatcher** (`core/state.py`): loop único de 2 s que faz duas coisas. (1) Botões com `state` (`mic_muted`/`audio_muted`) refletem fato real do PC — providers consultam `wpctl` (PipeWire) ou `pactl` (PulseAudio) e fazem broadcast de `state.update` quando muda, mais um push pós-trigger (`push_soon`). (2) **Sync de edições à mão**: compara o `mtime` do `profiles.json`; se mudou fora do app (editor de código), recarrega e propaga como `deck.layout` com `id: "file-sync"`. Após um `deck.save` o WS chama `mark_config_synced()` para que a própria escrita não seja vista como edição externa.

**Pareamento** (`core/pairing.py`): token único no `secret.token`, comparado com `secrets.compare_digest`. Quem apresenta token válido entra em `devices.json` e dispara uma notificação desktop (`notify-send`, best-effort) — **não** há prompt bloqueante (ADR 7). Revogar tudo: `--reset-pairing` (token novo + esquece dispositivos).

**TLS opcional** (`core/tls.py`): `--tls` serve HTTPS com um CA + certificado de servidor **gerados localmente via `cryptography`** (sem mkcert nem `sudo`), guardados em `~/.config/prodeck/tls/`. O certificado cobre todos os IPs locais (SAN, de `all_lan_ips()`) e regenera quando a rede muda; o CA é estável. É o que permite o Chrome instalar a PWA em tela cheia (contexto seguro) e o Wake Lock. Para o onboarding ser por QR e **sem avisos**, com `--tls` o agente sobe **dois servidores** (`main.py:_serve_with_tls`): o **app** em HTTPS na `port+1` (PWA + WS, via `create_app`) e um **app de setup** leve em HTTP na `port` (`create_setup_app`) que serve o `/qr` (dois QRs por rede: instalar o `/rootCA.pem` + abrir o app) sem topar aviso de certificado. O celular instala o `rootCA.pem` uma vez; o front deriva `wss://` de `location.protocol` sozinho.

**Front** (`app/src/`): Zustand (`store/useDeck.ts`) guarda conexão, layout, edição e estados; `ws/client.ts` faz reconexão com backoff exponencial + RTT. Edições são **otimistas**: `apply()` muda o estado local e dispara `deck.save`; se o agente responder `error`, o front mostra toast e re-sincroniza com `deck.get`. Toda transformação de config é função **pura e imutável** em `lib/deckOps.ts` (testada isoladamente em `tests/deckOps.test.ts`) — regras de UX (ex.: "não excluir a última página") moram lá e viram `Error` com mensagem amigável. O token chega pela URL do QR (`?token=`), é salvo em `localStorage` e removido da barra de endereço (`lib/identity.ts`).

## Convenções e armadilhas

- O `vite build` apaga e reescreve `agent/prodeck_agent/static/` (`emptyOutDir`). Esse diretório **é** o build versionado servido em produção; não edite à mão.
- Documentação de design e ADRs em `docs/` (pt-BR). `docs/03-arquitetura.md` é o mapa canônico — protocolo, modelo de dados e decisões registradas.
- O projeto está em X11 com `pynput` direto; não há abstração de backend de teclado por plataforma (YAGNI até precisar de Wayland).
- Tudo em português do Brasil: mensagens, logs (`loguru`), comentários e UI.
