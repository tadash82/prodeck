# ProDeck — Deck de Produtividade no Celular

> Nome provisório. "Stream Deck" é marca registrada da Elgato — renomear antes de publicar.
> Outras ideias: TaskDeck, DeckPad, LaunchDeck, Comando.

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

```bash
cd agent && uv run prodeck-agent
```

No celular (mesma rede do PC): abra `http://localhost:8710/qr` no PC e escaneie o QR da rede correta — o endereço já leva o token de pareamento. Depois use "Adicionar à tela inicial" para virar app fullscreen.

- Botões: edite `~/.config/prodeck/profiles.json` (recarregue o app para ver as mudanças)
- Token novo / esquecer dispositivos: `uv run prodeck-agent --reset-pairing`
- Desenvolvimento da PWA: `cd app && npm run dev` (proxy para o agente na 8710); mudou modelo Pydantic → rode `scripts/gen-types.sh`; `npm run build` publica no agente

## Status

- [x] Documentação e plano
- [x] Fase 0 — Prova de conceito (toque no celular abre o VSCode no PC) — concluída em 2026-06-11
- [ ] Fase 1 — MVP utilizável no dia a dia
- [ ] Fase 2 — Edição de botões pelo próprio app
- [ ] Fase 3 — Macros, botões com estado, tray
- [ ] Fase 4 — Polimento e distribuição (v1.0)
