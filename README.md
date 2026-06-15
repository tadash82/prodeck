# ProDeck — Deck de Produtividade no Celular

Transforme o celular (ou um tablet velho) em um painel de botões touch que controla o seu PC pela rede Wi-Fi: abrir o VSCode em um projeto, abrir pastas, disparar macros, rodar scripts, controlar mídia — com foco em **produtividade de desenvolvedor**, não em streaming.

```
┌────────── Celular ──────────┐                ┌───────────── PC ─────────────┐
│   PWA (React + Tailwind)    │   Wi-Fi (LAN)  │   Agente (Python + FastAPI)  │
│   grid de botões touch      │ ◄──WebSocket──►│   executa as ações           │
└─────────────────────────────┘     JSON       └──────────────────────────────┘
```

## Stack escolhida (resumo da decisão)

| Camada | Tecnologia | Por quê |
|---|---|---|
| Agente no PC | **Python 3.12 + FastAPI** | Você já domina Python; FastAPI serve HTTP + WebSocket + a própria PWA num processo só |
| App no celular | **PWA (React + Vite + Tailwind + Motion)** | Tela bonita sem app store: escaneia um QR code e está usando; funciona em Android, iOS e tablets |
| Comunicação | **WebSocket (JSON) na rede local** | Bidirecional (botões podem receber estado do PC), latência < 5 ms na LAN |
| Evolução futura | Flutter (opcional, Fase 5) | Se um dia precisar de recursos nativos; o agente e o protocolo permanecem os mesmos |

A análise completa das alternativas (Flutter, React Native, Kivy…) está em [docs/02-analise-de-tecnologias.md](docs/02-analise-de-tecnologias.md).

## Documentação

| Documento | Conteúdo |
|---|---|
| [01 — Visão e conceito](docs/01-visao-e-conceito.md) | O que é, para quem, casos de uso, concorrentes |
| [02 — Análise de tecnologias](docs/02-analise-de-tecnologias.md) | Comparativo das opções e justificativa da stack |
| [03 — Arquitetura](docs/03-arquitetura.md) | Componentes, protocolo, modelo de dados, segurança |
| [04 — Plano de desenvolvimento](docs/04-plano-de-desenvolvimento.md) | Fases, entregáveis, critérios de aceite, riscos |

## Como rodar

Instalar o comando globalmente (a PWA vem embutida no pacote):

```bash
uv tool install ./agent                   # do source (após publicar: uv tool install prodeck-agent)
prodeck-agent                             # 1º plano: abre a página de pareamento no navegador (--no-open desliga)
prodeck-agent --tls                       # HTTPS: instala a PWA em tela cheia (ver "Instalar como app")
prodeck-agent --install-service           # autostart via systemd (acrescente --tls p/ HTTPS no boot)
```

Na primeira instalação o `uv` pode pedir `uv tool update-shell` (uma vez) para
deixar `~/.local/bin` no PATH. Para desenvolver sem instalar, rode do source:

```bash
cd agent && uv run prodeck-agent
```

No celular (mesma rede do PC): abra `http://localhost:8710/qr` no PC e escaneie o QR da rede correta — o endereço já leva o token de pareamento. Para abrir em tela cheia (sem a barra do navegador), veja [Instalar como app](#instalar-como-app-tela-cheia).

**Três jeitos de configurar os botões** — todos sincronizam com todos os dispositivos na hora:

1. **Pelo celular**: toque no lápis (ou segure um botão) — editor com ações, macros, 200k ícones e cores. Tem **seletor de apps instalados** (já traz o ícone do programa), **atalhos prontos** (mutar som/mic, volume, bloquear tela — já com o comando certo da sua máquina) e um botão **"Testar"** que executa a ação na hora, sem salvar.
2. **Pelo navegador do PC**: abra `http://localhost:8710/qr` e clique em **"Abrir o deck aqui"** — a mesma PWA roda no desktop, sem precisar copiar token.
3. **No editor de código**: salve `~/.config/prodeck/profiles.json` — o agente detecta e replica em até 2 s.

Tipos de ação: programa, pasta, URL, atalho de teclado, texto (snippet), shell (opt-in: "Permitir ações shell" no gerenciador) e macro (sequência com esperas). Botões podem refletir estado real do PC (mic/áudio mutado). Deslize para a esquerda/direita troca de página.

**Aparência e layout** (lápis → gerenciador): tema **claro/escuro/automático**, **cor de destaque** e espaçamento — salvos no próprio aparelho; e **grade configurável** por página (colunas × linhas, 1–8 × 1–10), com "Reorganizar botões" para distribuir sem buracos. Os botões preenchem a tela e se reajustam ao girar (retrato/paisagem).

### Instalar como app (tela cheia)

Adicionar a PWA à tela inicial abre o deck **sem a barra do navegador**. O Chrome (Android) só oferece **"Instalar app"** em **contexto seguro** — `localhost` ou **HTTPS**. Por `http://<ip>:8710` (HTTP) ele trata como site comum e o atalho abre dentro do navegador (com a barra).

Rode com **`--tls`** — o agente gera um certificado local (sem instalar nada no sistema, sem `sudo`) e sobe um **assistente de pareamento**:

```bash
prodeck-agent --tls
```

Aí ele serve o deck em **HTTP** (porta 8710 — configurar pelo PC, sem avisos) e **HTTPS** (porta 8711 — PWA no celular). No PC, abra **`http://localhost:8710/qr`** — aparecem, por rede, dois QRs. No celular, **uma vez só**:

1. Escaneie **"instalar certificado"** → baixa o `rootCA.pem` → instale em Configurações → Segurança → Instalar certificado → Certificado CA.
2. Escaneie **"abrir o ProDeck"** → o app abre já confiável (cadeado) → menu ⋮ → **"Instalar app"** → tela cheia.

Sem digitar token nem topar avisos de "conexão não segura". O certificado fica em `~/.config/prodeck/tls/`, cobre todos os IPs locais e regenera sozinho se a rede mudar.

> **Configurar pelo PC:** abra **`http://localhost:8710/qr`** e clique em **"Abrir o deck aqui"** (não precisa copiar token). O deck roda em HTTP no PC, sem avisos, e tudo que você muda sincroniza com o celular na hora.

Úteis:

- Token novo / esquecer dispositivos: `uv run prodeck-agent --reset-pairing`
- Desenvolvimento da PWA: `cd app && npm run dev` (proxy para o agente na 8710); mudou modelo Pydantic → rode `scripts/gen-types.sh`; `npm run build` publica no agente
- Testes: `cd agent && uv run pytest` · `cd app && npm test`
- **Publicar no PyPI** (mantenedor): `cd app && npm run build` (se mexeu no front) → `cd agent && uv build && uv publish` (precisa de token PyPI). A PWA já vai embutida no wheel.

## Solução de problemas

**O celular não acha o agente / o QR não conecta**
- Confirme que celular e PC estão na **mesma rede**. Cuidado com redes dual-WAN/mesh: se o Wi-Fi do celular sai por outro modem (load balancer, pfSense), ele pode estar do *lado WAN* e sem rota até o PC. Teste conectando os dois ao mesmo Wi-Fi, ou configure port forward / reserva no roteador.
- O endereço `/qr` mostra **um QR por interface de rede** — escaneie o da rede que o celular realmente usa.
- **Firewall**: libere a porta do agente. No Ubuntu: `sudo ufw allow 8710/tcp`.
- **AP isolation** (isolamento de clientes) no roteador bloqueia dispositivos entre si — desative-o para a rede usada.

**Conectava e parou depois de reiniciar o PC**
- Se o IP do PC mudou (DHCP), o atalho salvo no celular aponta para o endereço antigo. Faça **reserva de DHCP / IP fixo** para o PC. A PWA mostra "agente não encontrado" — basta reabrir `/qr` e reescanear.

**Atalhos de teclado (`hotkey`/`text`) não funcionam**
- O agente injeta teclas via `pynput` em **X11**. Em sessão **Wayland** isso é restrito pelo compositor — use uma sessão Xorg (as demais ações continuam funcionando). Suporte a Wayland via ydotool/portal está no backlog.
- **Atalho global do desktop** (abrir terminal, bloquear tela, teclas de mídia) por `hotkey` **não funciona**: o sistema captura essas combinações antes, e a injeção não as dispara. Use a ação **Programa** com o comando direto, ou os **"Atalhos prontos"** do editor (terminal → `gnome-terminal`, bloquear → `loginctl lock-session`, mídia → `wpctl`/`pactl`). O `hotkey` serve para atalhos que o **app em foco** entende (Ctrl+S, Ctrl+C).

**O botão de mute não reflete o estado real do mic/áudio**
- O estado vem de `wpctl` (PipeWire) com fallback para `pactl` (PulseAudio). Garanta que um dos dois esteja instalado e no PATH.

**O ícone da bandeja não aparece (GNOME)**
- A bandeja é best-effort; no GNOME depende da extensão **AppIndicator**. O caminho garantido de "estar sempre rodando" é o serviço: `prodeck-agent --install-service`.

**A tela do celular apaga durante o uso**
- Em HTTPS (`--tls`) a PWA usa a **Screen Wake Lock API** nativa, mais confiável. Em HTTP cai no NoSleep.js (alguns navegadores exigem uma interação antes de ativar).

**`code` (ou outro programa) não abre ao tocar o botão**
- O comando precisa existir no PATH do agente. Algumas máquinas têm `code-insiders` em vez de `code` — ajuste a ação do botão para o binário correto.

**Não aparece "Instalar app" / abre com a barra do navegador**
- O Chrome instala a PWA em tela cheia só a partir de **HTTPS** (ou `localhost`). Por `http://<ip>` ele trata como site comum — dá para "Adicionar à tela inicial", mas o atalho abre dentro do navegador. A instalação completa (sem barra) vem com o **TLS opcional** (`--tls`, certificado local gerado pelo próprio agente). Ver [Instalar como app](#instalar-como-app-tela-cheia).

## Status

- [x] Documentação e plano
- [x] Fase 0 — Prova de conceito (toque no celular abre o VSCode no PC) — 2026-06-11
- [x] Fase 1 — MVP: 4 ações, pareamento por token, grid React — 2026-06-11
- [x] Fase 2 — Editor de botões no celular, perfis/páginas, sincronização — 2026-06-11
- [x] Fase 3 — Macros, shell/texto, botões com estado, autostart (+ sync de edições à mão) — 2026-06-11
- [x] Fase 4 — Polimento e distribuição (v1.0) — 2026-06-14:
  - [x] Nome definitivo (ProDeck), LICENSE MIT e guia de solução de problemas
  - [x] Temas (claro/escuro/auto), cor de destaque e grade (colunas × linhas) configurável
  - [x] TLS opcional (`--tls`, certificado local) → instalação da PWA em tela cheia
  - [x] Distribuição: pacote pronto pro PyPI (`uv tool install prodeck-agent`), PWA embutida
  - [x] Wake Lock nativo (Screen Wake Lock API em HTTPS; NoSleep.js de fallback)
  - [x] Editor: seletor de apps, atalhos prontos (mídia/sistema detectados), "Testar" ação, swipe entre páginas
- [ ] Fase 5 — Sob demanda: binário único (PyInstaller), suporte a Windows
