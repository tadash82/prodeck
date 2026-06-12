# 02 — Análise de Tecnologias

Contexto que pesa nas decisões:

- Você desenvolve em **Python** — quanto mais do "cérebro" do sistema ficar em Python, mais rápido você evolui o projeto sozinho.
- Requisito explícito: **tela bem bonita** no celular.
- Ambiente de desenvolvimento: Ubuntu GNOME em **X11**, Python 3.12.3 e Node 24 já instalados.
- O sistema tem duas metades independentes: o **app no celular** (mostra botões) e o **agente no PC** (executa ações). A escolha de tecnologia de cada metade é independente — o que as une é o protocolo.

---

## 1. App do celular

### Comparativo

| Critério | PWA (web) | Flutter | React Native / Expo | Kivy / KivyMD (Python) | BeeWare (Python) |
|---|---|---|---|---|---|
| Beleza da UI alcançável | ★★★★★ | ★★★★★ | ★★★★☆ | ★★☆☆☆ | ★☆☆☆☆ |
| Esforço até o MVP | **Dias** | Semanas | Semanas | Semanas | Meses |
| Curva vindo de Python | Média (JS/TS) | Média (Dart) | Média (JS/TS) | Nenhuma | Nenhuma |
| Distribuição | **QR code, pronto** | APK sideload ou Play Store | APK/Expo Go ou loja | APK via buildozer (doloroso) | Imaturo |
| iOS sem conta Apple (US$ 99/ano) | **Sim** (navegador) | Não | Não | Praticamente não | Não |
| Funciona em tablet velho / outro PC | **Sim, qualquer navegador** | Build por plataforma | Build por plataforma | Build por plataforma | — |
| Acesso a recursos nativos | Parcial (vibração, wake lock, fullscreen) | Total | Total | Parcial | Parcial |
| Risco de o projeto morrer na ferramenta | Baixo | Baixo | Médio | Alto (UI decepciona) | Alto |

### Recomendação: **PWA agora, Flutter como evolução opcional**

Um deck é, na essência, **um grid de botões touch em tela cheia** — exatamente o tipo de interface em que a web é imbatível em velocidade de desenvolvimento e qualidade visual:

1. **Distribuição zero**: o próprio agente Python serve a PWA. No celular: escaneia o QR → abre no navegador → "Adicionar à tela inicial" → vira um "app" fullscreen com ícone. Sem Google Play, sem Apple Developer Program, sem build de APK. Qualquer dispositivo com navegador (tablet Android velho, iPad, outro notebook) vira um deck.
2. **Tela bonita com pouco esforço**: Tailwind CSS + animações com Motion + 200 mil ícones via Iconify (inclusive logos reais: VSCode, Spotify, Docker, GitHub…). O resultado visual compete com app nativo para este tipo de UI.
3. **As APIs web cobrem o que o deck precisa**: `navigator.vibrate()` para feedback háptico (Android), Wake Lock / NoSleep para a tela não apagar, Fullscreen API, Screen Orientation.
4. **Atualização instantânea**: atualizou o agente no PC, o app do celular já está novo. Sem republicar nada.
5. **Caminho de evolução preservado**: se um dia precisar de recursos nativos (widget na home, atalho físico, NFC), escreve-se um app Flutter **reaproveitando 100% do agente e do protocolo**. Nada do trabalho é jogado fora.

**Por que não Kivy/BeeWare, que manteriam Python?** Honestidade técnica: a UI do Kivy tem aparência datada e o empacotamento Android com buildozer é notoriamente frustrante; BeeWare ainda é imaturo para produção. Com o requisito "tela bem bonita", Python-no-celular é a opção que mais provavelmente mataria o projeto. Python brilha na outra metade (o agente).

**Por que não Flutter já no MVP?** Flutter entrega UI belíssima, mas exige aprender Dart + toolchain mobile + assinar/instalar APKs antes do primeiro botão funcionar. A PWA entrega o mesmo resultado visual para este caso de uso com uma fração do atrito — e Flutter continua disponível na Fase 5 se fizer sentido.

### Stack da PWA

| Peça | Escolha | Papel |
|---|---|---|
| Build | **Vite** | Dev server rápido, build estático que o agente serve |
| UI | **React 18 + TypeScript** | Maior ecossistema/documentação; TS dá a segurança de tipos que você conhece do Python |
| Estilo | **Tailwind CSS v4** | Produtividade para tema escuro, grids e estados |
| Animação | **Motion** (ex-Framer Motion) | Animação de press, transição entre páginas |
| Ícones | **Iconify** (`@iconify/react`) | 200k+ ícones, busca embutida no futuro editor |
| Estado | **Zustand** | Store simples (conexão, layout, perfil ativo) |
| PWA | **vite-plugin-pwa** | Manifest + service worker (modo fullscreen, ícone) |
| Drag & drop (Fase 2) | **dnd-kit** | Reordenar botões no editor |

> Alternativa válida: **Svelte** no lugar de React (mais simples, menos boilerplate). React ganha aqui por volume de documentação e bibliotecas (dnd-kit, Iconify) — mas se você preferir Svelte ao experimentar, a troca no início custa pouco.

---

## 2. Agente do PC

### Comparativo

| Critério | Python | Go | Rust | Node.js |
|---|---|---|---|---|
| Seu domínio atual | ★★★★★ | ☆ | ☆ | ★★☆ |
| Velocidade de desenvolvimento | ★★★★★ | ★★★ | ★★ | ★★★★ |
| Distribuição (binário único) | ★★★ (PyInstaller) | ★★★★★ | ★★★★★ | ★★★ |
| Bibliotecas de automação de SO | ★★★★★ | ★★★ | ★★★ | ★★★ |
| Extensibilidade por plugins do usuário | ★★★★★ (é Python!) | ★★ | ★★ | ★★★ |
| Consumo de RAM ocioso | ~50–80 MB | ~10 MB | ~5 MB | ~60 MB |

### Recomendação: **Python 3.12 + FastAPI** — sem hesitação

O agente é o componente que você vai mexer toda semana (novas ações, integrações). Em Python você tem velocidade máxima, o ecossistema de automação é maduro, e "plugins em Python" vira um diferencial do produto para o público dev. Go/Rust dariam um binário menor — irrelevante perto do custo de aprender uma stack nova para um projeto que precisa chegar ao MVP.

### Stack do agente

| Peça | Escolha | Papel |
|---|---|---|
| Gerenciador | **uv** | Padrão atual para projetos Python (lock, venv, `uv run`) |
| Servidor | **FastAPI + Uvicorn** | HTTP (serve a PWA, pareamento) + **WebSocket** no mesmo processo |
| Validação/Schema | **Pydantic v2** | Modelos do protocolo e da configuração; gera JSON Schema |
| Abrir apps/pastas/URLs | `subprocess` + `xdg-open` (Linux), `start` (Win), `open` (mac) | Núcleo das ações — abstraído por SO |
| Teclado/atalhos | **pynput** (X11/Win/mac) | Injeção de hotkeys. Ver nota Wayland abaixo |
| Bandeja do sistema | **pystray** + Pillow | Ícone, status, "mostrar QR", sair |
| QR code | **qrcode[pil]** | Pareamento (também em ASCII no terminal) |
| Config | JSON em `~/.config/prodeck/` | Perfis, dispositivos pareados, com campo `version` |
| Logs | **loguru** | Log de cada ação executada |
| Testes | **pytest** | Executores com subprocess mockado |
| Empacote (Fase 4) | **pipx/uv tool install** primeiro; PyInstaller depois | Público dev aceita `pipx install`; binário vem no polimento |

> **Nota X11/Wayland**: seu Ubuntu está em **X11**, então `pynput` cobre atalhos de teclado sem fricção. Se você (ou outro usuário) migrar para Wayland, injeção global de teclado exige `ydotool`/portal — por isso o agente abstrai isso num `InputBackend` trocável. Importante: **só a ação `hotkey` depende disso**; abrir apps, pastas e URLs funciona igual em qualquer sessão.

---

## 3. Comunicação celular ↔ PC

| Opção | Veredito | Motivo |
|---|---|---|
| **WebSocket (JSON)** | ✅ **Escolhido** | Bidirecional (PC pode atualizar estado dos botões em push), latência < 5 ms na LAN, reconexão simples, nativo no navegador e no FastAPI |
| HTTP REST puro | ❌ | Sem push do servidor; polling desperdiça bateria |
| MQTT | ❌ | Exige broker — uma peça a mais sem benefício aqui |
| gRPC | ❌ | Overkill; suporte em navegador requer proxy (grpc-web) |
| Bluetooth | ❌ | Pareamento chato, alcance menor, Web Bluetooth instável — Wi-Fi local resolve |

**Descoberta do agente:** QR code contendo `http://IP:PORTA/?token=...` (primário — funciona em qualquer celular) + digitação manual como fallback. mDNS/zeroconf fica como melhoria para o futuro app nativo — navegadores não resolvem service discovery de forma confiável.

**Formato das mensagens:** JSON com envelope tipado (`{type, id, payload}`), versionado desde o dia 1. Os modelos Pydantic geram JSON Schema, e dele geram-se os tipos TypeScript da PWA (`json-schema-to-typescript`) — **uma fonte de verdade para o protocolo**, sem dessincronizar as duas pontas.

### A pegadinha do HTTPS local (documentada para não surpreender)

Servir a PWA via `http://192.168.x.x` (sem TLS) tem duas consequências que **têm solução, mas precisam estar no radar**:

1. **Wake Lock API exige contexto seguro (HTTPS)** → no MVP, manter a tela acesa usa a técnica do NoSleep.js (vídeo mudo em loop), que funciona em HTTP.
2. **Instalação PWA "completa"** (service worker) também pede HTTPS → em HTTP, o "Adicionar à tela inicial" ainda funciona como atalho fullscreen, suficiente para o MVP.

Na Fase 4, o agente pode gerar certificado TLS próprio (mkcert) para quem quiser a experiência PWA completa. Não bloqueia nada antes disso.

---

## 4. Resumo da decisão

```
Celular:  PWA — Vite + React + TS + Tailwind + Motion + Iconify   (bonita e sem loja)
PC:       Python 3.12 + FastAPI + Pydantic + pynput + pystray     (seu território)
Conexão:  WebSocket JSON na LAN, pareado por QR code + token      (simples e rápido)
Futuro:   Flutter reusando agente e protocolo, se precisar        (nada se perde)
```
