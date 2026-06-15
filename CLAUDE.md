# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

ProDeck transforma o celular num "Stream Deck" touch que controla o PC pela LAN. Monorepo com dois pacotes: `agent/` (Python/FastAPI que roda no PC e executa as ações) e `app/` (PWA React que roda no celular/navegador). O agente **serve a própria PWA** — não há app de loja, o build do front sai dentro do pacote Python.

## Comandos

```bash
# Rodar o agente (imprime QR + URLs de pareamento no terminal)
cd agent && uv run prodeck-agent            # use --no-tray, --reset-pairing, --port N, --tls, --no-open
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

**Protocolo WS** (`server/ws.py`): envelope único `{ v, type, id, payload }` nos dois sentidos; `id` correlaciona requisição/resposta. Toda conexão começa com `hello` (token); sem handshake válido o socket é fechado com code 4401. Mensagens principais: `deck.get`/`deck.layout` (layout), `action.trigger`/`action.result` (executar botão), `action.test` (roda uma ação avulsa do editor sem salvar — responde `action.result` com `button_id: "__test__"`), `deck.save` (editar config), `state.update` (estado ao vivo), `ping`/`pong` (RTT). O `ConnectionManager` faz broadcast: ao salvar, os **outros** dispositivos recebem `deck.layout` com `id: "broadcast"`.

**Endpoints HTTP auxiliares** (`server/app.py`, autenticados por token via `secrets.compare_digest`, senão 401): `GET /apps` lista apps instalados (`.desktop`, `core/apps.py`) com ícone, pro seletor do editor; `GET /presets` devolve **atalhos prontos** detectados na máquina — mídia (`core/audio.py`: `wpctl`/`pactl`) + sistema (`core/system.py`: bloquear via `loginctl`/`xdg-screensaver`, print). O editor (`QuickActions.tsx`) preenche o botão num toque; `default_config()` usa as mesmas detecções. `GET /plugins` lista as ações de plugins instalados (`core/plugins.py`) e seus campos, pro editor (`PluginEditor.tsx`).

**Ações como união discriminada** (`core/models.py`, `core/engine.py`): cada `Action` é discriminada por `type` (`open_app`, `open_path`, `open_url`, `hotkey`, `text`, `shell`, `macro`, `plugin`). `macro` é uma lista de passos (ações básicas + `delay`). Adicionar um tipo novo no core = nova classe Pydantic na união + executor registrado em `default_engine()`. Executores são funções **síncronas** que levantam exceção em falha; o engine roda cada uma em `asyncio.to_thread` para não travar o event loop.

**Plugins** (`core/plugins.py`): ações de **pacotes externos** sem tocar no core. Um pacote publica um entry point no grupo `prodeck.actions` apontando para um `ActionPlugin` (`name`, `label`, `icon`, `fields`, `run`). O protocolo não muda: há um único tipo de ação `plugin` (`{ name, params }`); o engine despacha pelo `name` (`plugin_executor`), e o editor descobre os plugins e renderiza seus campos via `GET /plugins`. Plugin quebrado é ignorado com aviso. Exemplo que acompanha o agente: `prodeck_agent/plugins/notify.py` (entry point no `pyproject.toml`). Ver ADR 14.

**Segurança do `command`**: `command` é sempre **lista de argumentos** → `subprocess` sem shell, sem injeção. A ação `shell` (string única, roda no shell) é a exceção, barrada por `allow_shell` na config (padrão `false`) e checada no engine antes de executar. `allow_shell` é editável pelo próprio app — é fricção consciente, não barreira de segurança (`open_app` já roda binários arbitrários; o modelo de ameaça é o dispositivo pareado, ver ADR 10 em `docs/03-arquitetura.md`).

**ConfigStore** (`core/config.py`): persiste `profiles.json`, `devices.json` e `secret.token` em `~/.config/prodeck` (override via env `PRODECK_CONFIG_DIR`). Escrita é atômica (`tmp` + `os.replace`) e gera `.bak`. Há `_migrate()` versionado (`version` no topo do JSON) para evoluir o formato sem quebrar configs antigas. `default_config()` detecta binários da máquina (`shutil.which`) para montar botões que de fato funcionam.

**StateWatcher** (`core/state.py`): loop único de 2 s que faz três coisas. (1) Botões com `state` (`mic_muted`/`audio_muted`) refletem fato real do PC — providers consultam `wpctl` (PipeWire) ou `pactl` (PulseAudio) e fazem broadcast de `state.update` quando muda, mais um push pós-trigger (`push_soon`). (2) **Sync de edições à mão**: compara o `mtime` do `profiles.json`; se mudou fora do app (editor de código), recarrega e propaga como `deck.layout` com `id: "file-sync"`. Após um `deck.save` o WS chama `mark_config_synced()` para que a própria escrita não seja vista como edição externa. (3) **Perfil automático** (`core/window.py`): se `config.auto_profile` tem regras e a janela em foco (Xlib, só X11) mudou e casa um `match`, ativa aquele perfil e propaga `deck.layout` com `id: "auto-profile"`. Só age na mudança de janela (não briga com troca manual) e só com dispositivo conectado.

**Pareamento** (`core/pairing.py`): token único no `secret.token`, comparado com `secrets.compare_digest`. Quem apresenta token válido entra em `devices.json` e dispara uma notificação desktop (`notify-send`, best-effort) — **não** há prompt bloqueante (ADR 7). Revogar tudo: `--reset-pairing` (token novo + esquece dispositivos).

**TLS opcional** (`core/tls.py`): `--tls` serve HTTPS com um CA + certificado de servidor **gerados localmente via `cryptography`** (sem mkcert nem `sudo`), guardados em `~/.config/prodeck/tls/`. O certificado cobre todos os IPs locais (SAN, de `all_lan_ips()`) e regenera quando a rede muda; o CA é estável. É o que permite o Chrome instalar a PWA em tela cheia (contexto seguro) e o Wake Lock. Com `--tls`, o **mesmo app** é servido por **dois listeners no mesmo event loop** (`main.py:_serve_with_tls`, via `asyncio.gather` + signal handler único): **HTTP na `port`** (configurar pelo navegador do PC, sem avisos de certificado) e **HTTPS na `port+1`** (PWA em tela cheia no celular). Um loop só garante que o broadcast entre dispositivos funcione nos dois lados; o `lifespan` é idempotente (o watcher sobe uma vez, embora rode 2×). O `/qr` mostra, por rede, o QR de instalar o `/rootCA.pem` (HTTP) e o de abrir o app (HTTPS); o celular instala o `rootCA.pem` uma vez; o front deriva `wss://` de `location.protocol` sozinho.

**Front** (`app/src/`): Zustand (`store/useDeck.ts`) guarda conexão, layout, edição e estados; `ws/client.ts` faz reconexão com backoff exponencial + RTT. Edições são **otimistas**: `apply()` muda o estado local e dispara `deck.save`; se o agente responder `error`, o front mostra toast e re-sincroniza com `deck.get`. Toda transformação de config é função **pura e imutável** em `lib/deckOps.ts` (testada isoladamente em `tests/deckOps.test.ts`) — regras de UX (ex.: "não excluir a última página") moram lá e viram `Error` com mensagem amigável. O token chega pela URL do QR (`?token=`), é salvo em `localStorage` e removido da barra de endereço (`lib/identity.ts`).

## Convenções e armadilhas

- O `vite build` apaga e reescreve `agent/prodeck_agent/static/` (`emptyOutDir`). Esse diretório **é** o build versionado servido em produção; não edite à mão.
- Documentação de design e ADRs em `docs/` (pt-BR). `docs/03-arquitetura.md` é o mapa canônico — protocolo, modelo de dados e decisões registradas.
- O projeto está em X11 com `pynput` direto; não há abstração de backend de teclado por plataforma (YAGNI até precisar de Wayland).
- **`hotkey` não dispara atalho GLOBAL do desktop** (super+l, ctrl+alt+t, PrintScreen): o compositor captura essas combinações por keycode e a injeção do pynput não casa com o grab — só funciona em atalho que o app em **foco** interpreta. Para abrir terminal/bloquear/print/mídia, use ação `open_app` com comando direto (detectado em `core/system.py`/`core/audio.py`, oferecido em `/presets`). O editor avisa quando um `hotkey` parece global (`looksGlobalHotkey`). Ver ADR 13.
- Tudo em português do Brasil: mensagens, logs (`loguru`), comentários e UI.
