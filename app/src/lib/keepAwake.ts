import NoSleep from "nosleep.js";

/**
 * Mantém a tela acesa. O Wake Lock nativo exige HTTPS, então usamos o
 * NoSleep (vídeo mudo em loop), que funciona em HTTP — mas navegadores só
 * permitem ativá-lo a partir de um gesto do usuário, daí o primeiro toque.
 */
export function keepAwakeOnFirstTouch(): void {
  const noSleep = new NoSleep();
  const enable = () => {
    noSleep.enable().catch(() => {});
    document.removeEventListener("pointerdown", enable);
  };
  document.addEventListener("pointerdown", enable);
}
