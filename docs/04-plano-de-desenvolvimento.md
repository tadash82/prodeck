# 04 — Plano de Desenvolvimento

Estimativas assumem trabalho **part-time (~1–2 h/dia)** e são chutes honestos — sirva-se delas como proporção entre fases, não como promessa. Cada fase termina com algo **usável e demonstrável**; nenhuma fase depende de decisão futura.

```
Fase 0          Fase 1            Fase 2           Fase 3            Fase 4
Spike    ───►   MVP        ───►   Editor    ───►   Macros &   ───►   Polimento
1 fim de        2–3 semanas       2–3 semanas      Estado            & v1.0
semana                                             ~2 semanas        ~2 semanas
"o tubo         "uso no dia       "novo botão      "sequências,      "instalável,
funciona"       a dia"            sem editar       toggles, tray"    bonito, doc"
                                  JSON"
```

---

## Fase 0 — Spike: validar o tubo de ponta a ponta (1 fim de semana)

**Objetivo:** provar que tocar no celular executa algo no PC com latência imperceptível. Sem beleza, sem arquitetura final.

Tarefas:
1. `uv init` no `agent/` — FastAPI com um endpoint WS e **uma** ação hard-coded (`code ~/Projetos/StreamDeck`).
2. Uma página HTML crua (nem React ainda) com um botão gigante, servida pelo próprio FastAPI, conectando no WS.
3. Abrir no celular pelo IP, tocar, ver o VSCode abrir no PC.
4. Medir/observar: latência percebida, firewall do Ubuntu (ufw), celular e PC na mesma rede.

**Critério de aceite:** vídeo de 10 segundos: toque no celular → VSCode abre. ✅
**O que esta fase desarma:** os dois maiores riscos (rede local bloqueada e latência) morrem aqui, antes de qualquer investimento em UI.

> **✅ Concluída em 2026-06-11.** Aprendizados reais do spike:
> - Latência do tubo (WS + dispatch da ação) medida em ~1 ms localmente; imperceptível pelo celular na LAN.
> - O risco de rede se materializou numa forma não prevista: a casa tem **dual-WAN com pfSense** (modems Vivo + Claro balanceados) e o celular estava no Wi-Fi do modem — ou seja, **do lado WAN do load balancer**, sem rota para a LAN do PC. Solução de teste: notebook conectado ao mesmo Wi-Fi do celular. Em resposta, o `/qr` passou a exibir **um QR por interface de rede**.
> - `ufw` ativo bloqueava a porta (liberada com `sudo ufw allow 8710/tcp`); o comando `code` não existia no PATH (usado `code-insiders`).

---

## Fase 1 — MVP: usável no dia a dia (2–3 semanas)

**Objetivo:** você usar o deck **de verdade, todos os dias**, com botões configurados em JSON no PC.

Agente:
1. Modelos Pydantic (`Profile/Page/Button/Action` + mensagens do protocolo) e `profiles.json` com migração por `version`.
2. ActionRegistry com 4 executores: `open_app`, `open_path`, `open_url`, `hotkey` (pynput/X11).
3. Pareamento: token persistente, QR no terminal (`qrcode` em ASCII), confirmação do primeiro dispositivo, `devices.json`.
4. `action.result` com sucesso/erro de cada execução; log de ações com loguru.
5. Script `gen-types.sh` (Pydantic → JSON Schema → tipos TS).

PWA:
6. Projeto Vite + React + TS + Tailwind; cliente WS com handshake, reconexão automática com backoff e indicador de status.
7. **DeckGrid**: grid responsivo (CSS Grid), tema escuro, botões com ícone Iconify + cor + label, animação de press (Motion), feedback visual de sucesso/erro vindo do `action.result`, vibração no toque (Android).
8. Tela de conexão (primeiro acesso/desconectado) com instrução do QR.
9. Manter tela acesa (NoSleep.js) + meta tags fullscreen para "Adicionar à tela inicial".

**Critério de aceite:**
- Deck com ≥ 8 botões reais do seu fluxo (projetos, pastas, URLs, mute) usado por ≥ 3 dias seguidos.
- Derrubar o Wi-Fi do celular e voltar → reconecta sozinho em segundos, sem reload manual.
- Latência toque→ação < 150 ms percebidos na LAN.

**Fora desta fase (resistir à tentação):** editor visual, macros, múltiplos perfis na UI, tray.

> **✅ Concluída em 2026-06-11.** Conforme o plano, com um desvio consciente: a
> "confirmação no PC" do primeiro pareamento virou **notificação não bloqueante**
> (auto-aprovação com token) — ver ADR 7 no doc 03. Protocolo validado ao vivo:
> token inválido recusado, layout entregue, 24 testes. Tipos TS gerados dos
> modelos Pydantic desde o primeiro dia, como planejado.

---

## Fase 2 — Editor no app: novo botão sem tocar em JSON (2–3 semanas)

**Objetivo:** criar/editar botões pelo próprio celular. É o que separa "script pessoal" de "produto que outra pessoa consegue usar".

1. Modo edição na PWA: long-press abre o editor do botão.
2. Formulário por tipo de ação (campos dinâmicos conforme `type`), picker de ícones com busca (Iconify), seletor de cor.
3. Adicionar/remover/reordenar botões (dnd-kit), páginas e perfis; troca de perfil na UI.
4. `deck.save` no protocolo: agente valida com Pydantic, persiste com escrita atômica e backup automático do JSON anterior, e propaga `deck.layout` para todos os dispositivos conectados.

**Critério de aceite:** criar do zero, só pelo celular, um botão "abrir pasta X" funcional em < 1 minuto; config sobrevive a restart do agente; erro de validação aparece como mensagem amigável no app.

> **✅ Concluída em 2026-06-11.** Tudo do escopo: long-press/lápis, células
> vazias com "+", drag com troca de posições (dnd-kit), busca de ícones via API
> do Iconify, perfis/páginas e broadcast de `deck.layout` para todos os
> dispositivos (validado com dois clientes simultâneos). A validação Pydantic
> volta como erro amigável e o app ressincroniza. `DeckConfig` ganhou validação
> de ids duplicados.

---

## Fase 3 — Macros, estado e presença (≈ 2 semanas)

**Objetivo:** os recursos que fazem dizer "ok, isso substitui um Stream Deck".

1. Ação `macro`: sequência de passos com `delay`, execução assíncrona, resultado por passo.
2. Ação `shell` (opt-in, marcada como perigosa, sempre logada) e ação `text` (digitar snippet).
3. Botões **toggle** com estado (`state.update` via WS): ex. mute do mic mostrando estado real (pactl no Linux).
4. Ícone na bandeja (pystray): status, nº de dispositivos, "mostrar QR", revogar dispositivo, sair.
5. Autostart: systemd user service (`systemctl --user enable prodeck`).
6. Testes: pytest nos executores (subprocess mockado) e no fluxo de pareamento; vitest no cliente WS.

**Critério de aceite:** botão "Modo Trabalho" abre VSCode + terminal + 2 URLs em sequência confiável; botão de mute reflete o estado real do mic; agente sobe sozinho com a sessão.

> **✅ Concluída em 2026-06-11.** Desvios e aprendizados:
> - **PipeWire**: o Ubuntu atual não traz `pactl` — providers de estado usam
>   `wpctl` com fallback para pactl (descoberto em teste real).
> - **Bandeja**: best-effort — no GNOME depende da extensão AppIndicator; o
>   caminho garantido de presença é o serviço systemd (`--install-service`).
> - **Resultado por passo** da macro simplificado: a falha aponta o passo
>   ("passo 2 (open_url): …") em vez de stream de progresso.
> - **Extra fora do plano**: edições à mão no `profiles.json` sincronizam com
>   todos os dispositivos (watcher por mtime, 2 s) — pedido de uso real.
> - **Testes do app**: vitest cobre as operações puras (deckOps); testes do
>   cliente WS ficam para quando a lógica dele crescer.
> - Validado ao vivo: macro com delay de 400 ms (404 ms medidos), gate do shell
>   (off→bloqueado, on→executou), mute refletindo estado com push imediato.

---

## Fase 4 — Polimento e distribuição: v1.0 (≈ 2 semanas)

**Objetivo:** alguém que não é você instalar e usar.

1. Instalação: `pipx install` / `uv tool install` documentados; PyInstaller para binário único (Linux primeiro; Windows se houver demanda).
2. Build da PWA embutido no pacote Python (servida de `importlib.resources`).
3. TLS opcional via mkcert → Wake Lock nativo + instalação PWA completa (ver doc 02).
4. Temas (claro/escuro/cores de destaque), modo paisagem/tablet, ajuste de tamanho do grid.
5. README com GIF de demonstração, guia de troubleshooting (firewall, IP, X11/Wayland), licença (MIT), escolher o **nome definitivo** do projeto.
6. Suporte a Windows no agente (`start`, paths) — as abstrações por SO já existem desde a Fase 1.

**Critério de aceite:** uma pessoa de fora instala com ≤ 3 comandos seguindo só o README e cria o primeiro botão em < 5 minutos.

---

## Fase 5 — Futuro (backlog, sem compromisso)

Em ordem aproximada de valor:

- **Sistema de plugins** em Python (entry points): a comunidade adiciona ações sem tocar no core. É o diferencial estratégico do agente em Python.
- **App Flutter** nativo (reusa agente + protocolo) se surgir necessidade real: widgets na home, NFC, Bluetooth.
- Perfil automático por janela ativa (deck muda quando o VSCode ganha foco — fácil em X11, restrito em Wayland).
- Botões-widget com dados ao vivo (CPU/RAM, agenda, contador de PRs).
- Integrações: Home Assistant, KDE Connect, espelhar para OBS (aí sim, como plugin).
- Multi-PC: um celular controla várias máquinas (seletor de agente).
- Compartilhamento de perfis (exportar/importar JSON; futura "galeria").

---

## Riscos e mitigações

| Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|
| Migração futura para Wayland quebra `hotkey` | Média | Médio | `InputBackend` abstraído desde a Fase 1; só a ação hotkey depende dele; ydotool/portal documentados como caminho |
| Celular e PC em redes diferentes (AP isolation, VLANs, ou celular do lado WAN de um load balancer — **caso real na Fase 0**) | Média | Alto p/ usuário afetado | QR multi-interface já implementado; troubleshooting deve orientar: conectar PC ao mesmo Wi-Fi do celular, ou port forward no roteador/pfSense (solução permanente) |
| IP do PC muda (DHCP) e o QR salvo invalida | Média | Baixo | Instruir reserva DHCP/IP fixo; PWA mostra tela clara de "agente não encontrado" com re-pareamento fácil |
| Tela do celular apaga durante o uso | Alta | Médio | NoSleep.js no MVP; Wake Lock real com TLS na Fase 4 |
| iOS/Safari com quirks de PWA | Média | Baixo | Android é o alvo primário; testar iOS na Fase 4; nada no design depende de API exclusiva |
| Ação `shell` vira porta de abuso | Baixa | Alto | Opt-in, confirmação, log; nunca habilitada por padrão |
| Escopo crescer antes do MVP ("e se eu já fizer o editor…") | **Alta** | Alto | Este plano: fases fechadas com critérios de aceite; backlog explícito na Fase 5 |

## Métricas de sucesso

- **Latência** toque→ação < 150 ms na LAN.
- **Setup** de um dispositivo novo < 1 minuto (escanear QR → confirmar no PC → usar).
- **Uso real**: você usando diariamente a partir do fim da Fase 1 — o teste que importa.

---

## Primeiros comandos (quando sair da doc para o código — Fase 0)

```bash
cd ~/Projetos/StreamDeck
git init

# Agente
mkdir agent && cd agent
uv init --name prodeck-agent --python 3.12
uv add "fastapi[standard]" pydantic loguru qrcode pynput pystray

# (PWA entra na Fase 1)
cd .. && npm create vite@latest app -- --template react-ts
```
