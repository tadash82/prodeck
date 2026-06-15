# ProDeck Agent

Transforme o celular (ou um tablet velho) num **painel de botões touch** que controla o seu PC pela rede Wi-Fi: abrir projetos no editor, pastas, URLs, disparar macros, atalhos de teclado, controlar mídia — com foco em **produtividade de desenvolvedor**, não em streaming.

Sem app de loja: o agente roda no PC e **serve a própria PWA**. Você escaneia um QR no celular e está usando — o endereço já leva o token, não precisa digitar nada.

## Instalação

```bash
uv tool install prodeck-agent      # ou: pipx install prodeck-agent
prodeck-agent                      # imprime o QR + URLs de pareamento no terminal
```

No celular (mesma rede do PC), escaneie o QR. Para abrir em **tela cheia** (PWA instalada), rode `prodeck-agent --tls` e siga o assistente de pareamento.

## Comandos

| Comando | O que faz |
|---|---|
| `prodeck-agent` | roda em primeiro plano (QR e URLs no terminal) |
| `prodeck-agent --tls` | HTTPS + assistente de pareamento por QR (instala a PWA em tela cheia) |
| `prodeck-agent --install-service` | autostart via systemd de usuário (acrescente `--tls` p/ HTTPS no boot) |
| `prodeck-agent --reset-pairing` | gera token novo e esquece os dispositivos pareados |

Configure os botões pelo próprio celular (toque no lápis), pelo navegador do PC, ou editando `~/.config/prodeck/profiles.json` (sincroniza sozinho). O editor tem **seletor de apps instalados** (já traz o ícone do programa), **atalhos prontos** detectados na máquina (mutar som/mic, volume, bloquear tela) e botão **"Testar"** que roda a ação sem salvar. Tipos de ação: programa, pasta, URL, atalho de teclado, texto, shell (opt-in) e macro. Botões podem refletir estado real do PC (mic/áudio mutado).

## Requisitos

- **Python ≥ 3.12**, **Linux**. A ação de atalho de teclado (`hotkey`) usa X11; as demais funcionam também em Wayland.
- Atalhos de mídia/bloquear usam o que a máquina tiver: `wpctl` (PipeWire) ou `pactl` (PulseAudio) para áudio; `loginctl`/`xdg-screensaver` para bloquear. Detectados automaticamente.

## Documentação e roadmap

Código, arquitetura, plano de desenvolvimento e guia de solução de problemas: **https://github.com/tadash82/prodeck**

Licença: [MIT](https://github.com/tadash82/prodeck/blob/main/LICENSE).
