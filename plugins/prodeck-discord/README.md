# prodeck-discord

Plugin do [ProDeck](../../README.md) que adiciona botões para **mutar o microfone**
e **ensurdecer (deafen)** no Discord — controlando o estado *interno* do Discord
(o ícone do app muda), não só o mic do sistema. O botão ainda **acende** quando
você está mudo/ensurdecido, refletindo o estado real.

A integração fala o **RPC local** do Discord pelo socket IPC
(`$XDG_RUNTIME_DIR/discord-ipc-0`), sem tocar no core do agente. É um pacote
externo de verdade (ADR 14): registra duas ações no grupo de entry points
`prodeck.actions`.

## Por que precisa de um app no Discord (uma vez)

O Discord só libera o escopo `rpc` (necessário para mexer em mute/deafen) para o
**dono** de um app e seus testers — não para apps públicos não aprovados. Então
cada pessoa cria o próprio app no Discord Developer Portal e autoriza uma vez.

Também por design do Discord, alterações de voz via RPC **revertem quando o app
que as fez desconecta**. Por isso o plugin mantém uma conexão IPC **persistente**
viva enquanto o agente roda (o agente já é um serviço de longa duração).

## 1. Criar o app no Discord Developer Portal

1. Acesse <https://discord.com/developers/applications> → **New Application**, dê um nome (ex.: `ProDeck`).
2. Em **OAuth2 → Redirects**, clique **Add Redirect** e cadastre exatamente:
   ```
   http://localhost
   ```
   Salve. (Não é usado para navegar — o Discord exige um redirect válido na troca do token.)
3. Em **OAuth2** (ou na aba **General Information**), copie o **Client ID** e o **Client Secret** (em OAuth2; gere/“Reset Secret” se preciso).

> Você é o dono do app, então já está autorizado a usar o escopo `rpc`. Não
> precisa publicar nem aprovar nada.

## 2. Instalar o plugin no venv do agente

O plugin precisa estar no **mesmo** ambiente do agente para o entry point ser
descoberto. No monorepo, ele já está declarado como dependência opcional do
agente (grupo `plugins`):

```bash
cd agent
uv sync --group plugins      # instala o prodeck-discord (editável) no .venv do agente
```

## 3. Autorizar (uma vez)

Com o **Discord aberto e logado** no PC:

```bash
cd agent
uv run prodeck-discord-auth
# cole o Client ID e o Client Secret quando pedir
# — aparece um modal no Discord; clique em "Autorizar"
```

Isso salva `~/.config/prodeck/discord.json` (token + refresh, `chmod 600`). O
token é renovado sozinho depois.

Alternativa sem prompt:

```bash
PRODECK_DISCORD_CLIENT_ID=... PRODECK_DISCORD_CLIENT_SECRET=... uv run prodeck-discord-auth
```

## 4. Usar

Reinicie o agente para carregar o plugin e adicione os botões no editor:

```bash
systemctl --user restart prodeck
```

No editor do app, as ações **“Discord: Mutar mic”** e **“Discord: Ensurdecer”**
aparecem na lista de plugins. Para o botão **acender** quando estiver mudo,
defina o `state` do botão como `discord_muted` (ou `discord_deaf`).

## Resolução de problemas

- **“Discord não conectado”** ao tocar o botão: o Discord precisa estar **aberto**
  no PC. Confira o socket: `ls "$XDG_RUNTIME_DIR"/discord-ipc-*`.
- **Flatpak/Snap**: o socket fica em subpasta (`app/com.discordapp.Discord/` ou
  `snap.discord/`); o plugin já procura nesses lugares.
- **“token inválido”** nos logs: rode `prodeck-discord-auth` de novo.
- Acompanhe: `journalctl --user -u prodeck -f`.

## Desenvolvimento

```bash
cd agent && uv run python -m pytest ../plugins/prodeck-discord/tests
```
