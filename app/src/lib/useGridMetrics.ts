import { useEffect, useRef, useState } from "react";

import type { GridSize } from "../store/usePrefs";

/**
 * Calcula o tamanho de cada célula para o grid **caber por inteiro** no espaço
 * disponível, tanto em retrato quanto em paisagem/tablet: a célula é o menor
 * lado possível entre o limite de largura e o de altura. Isso resolve de uma só
 * vez "modo paisagem/tablet" (nunca estoura a tela) e "ajuste de tamanho"
 * (o preset escolhido define o teto e o espaçamento).
 */

const SIZING: Record<GridSize, { gap: number; max: number }> = {
  compact: { gap: 8, max: 88 },
  comfortable: { gap: 12, max: 116 },
  large: { gap: 16, max: 152 },
};
const MIN_CELL = 52;

export function useGridMetrics(cols: number, rows: number, size: GridSize) {
  const ref = useRef<HTMLDivElement>(null);
  const [box, setBox] = useState({ w: 0, h: 0 });

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const measure = () => setBox({ w: el.clientWidth, h: el.clientHeight });
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const { gap, max } = SIZING[size];
  const fitWidth = box.w ? (box.w - (cols - 1) * gap) / cols : max;
  const fitHeight = box.h ? (box.h - (rows - 1) * gap) / rows : max;
  const cell = Math.max(MIN_CELL, Math.min(max, Math.floor(Math.min(fitWidth, fitHeight))));
  const width = cell * cols + gap * (cols - 1);

  return { ref, cell, gap, width };
}
