import NoSleep from "nosleep.js";

/**
 * Mantém a tela do celular acesa. Prefere a **Screen Wake Lock API** nativa
 * (mais leve e confiável; exige HTTPS — daí o `--tls`) e cai no NoSleep.js
 * (vídeo mudo em loop) em HTTP ou navegadores sem a API. O lock nativo é
 * liberado quando a aba fica oculta, então é readquirido ao voltar à tela.
 */
export function keepAwake(): void {
  if ("wakeLock" in navigator) {
    nativeWakeLock();
  } else {
    noSleepFallback();
  }
}

function nativeWakeLock(): void {
  let sentinel: WakeLockSentinel | null = null;
  const acquire = async () => {
    if (sentinel || document.hidden) return;
    try {
      sentinel = await navigator.wakeLock.request("screen");
      sentinel.addEventListener("release", () => {
        sentinel = null;
      });
    } catch {
      // NotAllowedError etc. — tenta de novo no próximo gesto ou ao voltar à tela.
    }
  };
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) void acquire();
  });
  document.addEventListener("pointerdown", () => void acquire());
  void acquire();
}

function noSleepFallback(): void {
  // Navegadores só permitem ativar o NoSleep a partir de um gesto do usuário.
  const noSleep = new NoSleep();
  const enable = () => {
    noSleep.enable().catch(() => {});
    document.removeEventListener("pointerdown", enable);
  };
  document.addEventListener("pointerdown", enable);
}
