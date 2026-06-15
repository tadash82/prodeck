# 05 — Modo painel: abrir o deck no boot e manter o celular sempre ativo

Cenário: um **celular ou tablet dedicado** (aquele velho da gaveta) preso na mesa/parede, ligado no carregador, mostrando o deck o tempo todo — ligou o aparelho, o ProDeck já está na tela.

> **A limitação que define tudo:** a PWA do ProDeck é um app web. O Android **não** deixa um app web se abrir sozinho no boot (não existe API para isso). Então o "abrir no boot" é sempre feito por um **app auxiliar** no celular. Há dois caminhos, conforme o aparelho seja dedicado ou o seu de uso pessoal.

---

## Antes de começar

1. **Agente sempre no ar quando o PC liga.** Instale como serviço (sobe sozinho no login, fora de qualquer sandbox):
   ```bash
   prodeck-agent --install-service --tls
   ```
2. **IP fixo para o PC.** Faça **reserva de DHCP / IP fixo** no roteador. Sem isso, o IP do PC pode mudar e a URL salva no celular passa a apontar para o endereço errado.
3. **TLS ligado (`--tls`).** É o que dá **tela cheia** + **Wake Lock** (tela acesa) no celular. Veja [Instalar como app](../README.md#instalar-como-app-tela-cheia).
4. **Certificado instalado no celular** (o `rootCA.pem`, pelo assistente do `/qr`) — uma vez só.
5. **Anote a URL do deck**, que você pega no PC em `http://localhost:8710/qr` (ou no banner do agente). Ela tem este formato:
   ```
   https://<IP-DO-PC>:8711/?token=<SEU-TOKEN>
   ```
   > ⚠️ O `token` é um segredo de pareamento — não publique essa URL.

---

## Método A — Fully Kiosk Browser  *(recomendado para aparelho dedicado)*

O **Fully Kiosk Browser** (Play Store, gratuito; alguns extras são pagos) é feito exatamente para "aparelho fixo mostrando uma página o tempo todo": abre no boot, mantém a tela ligada, roda em tela cheia e se trava no app.

### Passo a passo

1. Instale o **Fully Kiosk Browser** e abra-o uma vez (o Android só entrega o evento de boot a apps já abertos pelo menos uma vez).
2. Conceda as permissões que ele pedir (sobreposição de tela, etc.).
3. Abra **Settings** (deslize da borda esquerda ou toque na engrenagem) e ajuste:
   - **Web Content → Start URL**: cole a URL do deck (`https://<IP>:8711/?token=...`).
   - **Device Management → Start on Boot** (*iniciar após o boot*): **ligado**.
   - **Power Settings (ou Screen) → Keep Screen On** (*manter tela ligada*): **ligado**.
   - **Web Browsing Settings → Fullscreen Mode** (e ocultar barras de status/navegação): **ligado**.
   - *(se o HTTPS reclamar)* **Advanced Web Settings → Ignore SSL/Certificate Errors**: ligue. Com o `rootCA` instalado normalmente nem precisa.
   - *(reconexão)* **Web Auto Reload → Reload on Connection Back / Reload on Idle**: recarrega se o Wi-Fi ou o PC caírem.
4. **Tire o Fully da otimização de bateria** (Configurações do Android → Bateria → Apps → Fully → "Sem restrição"). Senão o Android pode matá-lo e o boot-launch falha.
5. *(opcional, kiosk de verdade)* Para o botão Início não sair do app:
   - **Device Management → Run as Launcher / Set as Default Launcher**, ou
   - use o **fixar tela** do Android, ou o **Kiosk Mode** do Fully (com PIN para sair).
6. **Reinicie o aparelho** para testar: deve ligar já no deck.

### Dica
Deixe sempre no **carregador** (tela ligada o tempo todo consome). Um suporte/dock resolve.

---

## Método B — MacroDroid ou Tasker  *(leve, sem travar o aparelho)*

Para o **seu celular de uso pessoal**: aqui você só quer que o deck **abra** em certo momento, sem virar kiosk.

### Com MacroDroid (Play Store, gratuito)

1. Instale o **MacroDroid** e abra-o.
2. **Add Macro** → nova macro:
   - **Gatilho (Trigger):** *Device Boot* (dispositivo iniciado). *(ou prefira *Screen Unlocked* — abrir ao desbloquear.)*
   - *(opcional)* **Ação:** *Wait Before Next Action* ~10 s — dá tempo do Wi-Fi subir.
   - **Ação (Action):** *Launch Application* → selecione **ProDeck** (a PWA instalada aparece como app na lista).
3. Salve e **ative** a macro.
4. **Tire o MacroDroid da otimização de bateria** (mesmo motivo do Fully), senão o gatilho de boot pode não disparar.

*Tasker faz o mesmo:* Profile **Event → System → Device Boot** → Task **App → Launch App → ProDeck**.

---

## Manter a tela sempre ligada (resumo das opções)

| Como | Onde | Observação |
|---|---|---|
| **Wake Lock nativo** | automático com `--tls`, enquanto o deck está aberto | já vem de graça; é o motivo de usar HTTPS |
| **"Permanecer ativo"** | Android → Opções do desenvolvedor → *Stay awake while charging* | tela nunca apaga **ligado no carregador** |
| **Keep Screen On** | Fully Kiosk → Power Settings | controle fino (brilho, screensaver com detecção de movimento) |

Combinação típica do aparelho dedicado: **carregador + "Permanecer ativo" + Wake Lock** (ou o Keep Screen On do Fully).

---

## Solução de problemas

- **Não abre no boot:** o app auxiliar precisa ter sido **aberto ao menos uma vez** e estar **fora da otimização de bateria**.
- **Abre, mas dá erro de certificado:** confirme o `rootCA` em Configurações → Segurança → Credenciais/Certificados; ou ligue *Ignore SSL Errors* no Fully.
- **"Agente não encontrado" / não conecta:** IP do PC mudou (faça reserva de DHCP) ou o agente não está rodando — confira o serviço com `systemctl --user status prodeck`. O cliente já tenta reconectar sozinho (backoff); no Fully, ligue o auto-reload.
- **A tela ainda apaga:** ligue *Permanecer ativo* (Opções do desenvolvedor) **e** mantenha no carregador; o Wake Lock só age com o app aberto e visível.
- **iOS:** o iOS **não** permite auto-abrir no boot. Dá para instalar a PWA na tela inicial e usar o **Acesso Guiado** para travar no app, mas sem início automático — por isso o alvo deste guia é Android.

---

## Qual escolher

| Aparelho | Escolha |
|---|---|
| Celular/tablet **dedicado** (sempre na mesa/parede) | **Método A — Fully Kiosk** (boot + tela ligada + kiosk) |
| Seu **celular pessoal** | **Método B — MacroDroid** (só auto-abrir, sem travar) |
