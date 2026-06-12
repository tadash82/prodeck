# 01 — Visão e Conceito

## O problema

Trocar de contexto no PC desperdiça tempo e atenção: localizar a pasta do projeto, abrir o editor, subir o docker, abrir as três abas de sempre, ajustar o áudio para a reunião. Um Stream Deck físico resolve isso com botões dedicados, mas:

- Custa caro (R$ 800+ no Brasil) e tem poucos botões físicos.
- O ecossistema (Elgato, Touch Portal) é voltado para **streamers**: OBS, cenas, alertas.
- O suporte a Linux é fraco ou inexistente nas soluções comerciais.

Enquanto isso, todo mundo já tem na mesa um celular — ou um tablet velho na gaveta — com uma tela touch excelente parada.

## A solução

Um app no celular exibe um **grid de botões configuráveis**. Cada toque envia um comando via Wi-Fi para um **agente leve rodando no PC**, que executa a ação. Foco total em produtividade:

| Categoria | Exemplos de botão |
|---|---|
| Projetos | "VSCode · StreamDeck" → `code ~/Projetos/StreamDeck` |
| Pastas | "Downloads" → abre `~/Downloads` no gerenciador de arquivos |
| Macros | "Modo Trabalho" → abre VSCode + terminal + 3 abas do navegador, em sequência |
| Scripts | "git pull em tudo", "docker compose up", "backup agora" |
| Atalhos | Mute do microfone na reunião, print da tela, lock da sessão |
| Mídia | play/pause, volume, próxima faixa |
| Snippets | digita um texto padrão (e-mail de assinatura, comando longo) |
| Web | abre URLs recorrentes (dashboard, Jira, repositório) |

Botões são organizados em **páginas** e **perfis** (ex.: perfil "Dev", perfil "Reunião", perfil "Pessoal"), com ícones, cores e tema escuro caprichado.

## Princípios do produto

1. **Produtividade primeiro** — o usuário-alvo é dev/profissional, não streamer. Nada de integração com OBS no core (pode virar plugin um dia).
2. **Zero fricção de instalação no celular** — escaneou o QR code, está usando. Sem app store, sem conta, sem assinatura.
3. **Linux como cidadão de primeira classe** — o desenvolvimento acontece em Ubuntu/GNOME; Windows e macOS vêm na sequência (as APIs de SO ficam abstraídas desde o início).
4. **Configuração é dado, não código** — perfis e botões são JSON versionado, fácil de fazer backup e compartilhar.
5. **Extensível em Python** — a linguagem do dono do projeto. Novas ações devem ser fáceis de adicionar (registry de executores; sistema de plugins no futuro).
6. **Seguro por padrão** — o agente executa comandos no PC; pareamento obrigatório por token, confirmação no primeiro acesso, tudo restrito à rede local.

## Concorrentes e referências

| Produto | Modelo | Pontos fortes | Lacunas que exploramos |
|---|---|---|---|
| Elgato Stream Deck Mobile | Assinatura paga | Polido, ecossistema enorme | Caro, foco em streaming, sem Linux |
| Touch Portal | Freemium | Muitas integrações | UI datada, recursos-chave pagos, Linux limitado |
| Macro Deck 2 | Open source | Gratuito, plugins | Servidor só Windows |
| Deckboard | Freemium | Simples | Pouca evolução, foco em OBS |
| StreamPi | Open source | Multiplataforma | Projeto parado, UI JavaFX pesada |
| KDE Connect | Open source | Maduro, confiável | Comandos remotos são recurso secundário, sem grid customizável |

**Posicionamento:** open source, Linux-first, dev-friendly, mobile sem loja de aplicativos. Esse nicho está genuinamente vago.

## Escopo (atualizado em 2026-06-11, Fases 0–3 entregues)

**Já é:** grid bonito no celular executando ações no PC (programas, pastas, URLs, atalhos, snippets de texto, shell opt-in e macros multi-step), editor visual no próprio app (ícones, cores, drag-and-drop), perfis e páginas, botões com estado real do sistema (ex.: mute do microfone), pareamento por QR code e sincronização em tempo real entre todos os dispositivos — inclusive de edições feitas à mão no JSON pelo PC.

**Ainda não é (Fase 4 / backlog):** produto instalável por terceiros sem fricção (binário/pipx documentado), TLS local, temas, integração com OBS/Home Assistant, multi-PC, sistema de plugins, loja de perfis.

## Nome

A pasta do projeto se chama `StreamDeck`, mas **"Stream Deck" é marca da Elgato** — antes de publicar qualquer coisa, adotar um nome próprio. Nos documentos usamos **ProDeck** como codinome provisório.
