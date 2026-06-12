import { useRef } from "react";

/**
 * Long-press com cancelamento por movimento (scroll/drag não dispara).
 * O clique que o navegador emite ao soltar depois do long-press deve ser
 * ignorado pelo chamador via `firedRecently()`.
 */
export function useLongPress(onLongPress: () => void, ms = 450) {
  const timer = useRef<number | undefined>(undefined);
  const firedAt = useRef(0);

  const clear = () => {
    if (timer.current !== undefined) {
      window.clearTimeout(timer.current);
      timer.current = undefined;
    }
  };

  return {
    firedRecently: () => Date.now() - firedAt.current < 600,
    handlers: {
      onPointerDown: () => {
        clear();
        timer.current = window.setTimeout(() => {
          firedAt.current = Date.now();
          navigator.vibrate?.(30);
          onLongPress();
        }, ms);
      },
      onPointerUp: clear,
      onPointerLeave: clear,
      onPointerMove: clear,
    },
  };
}
