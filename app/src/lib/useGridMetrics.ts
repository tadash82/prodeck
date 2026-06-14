import { useEffect, useRef, useState } from "react";

import type { GridSize } from "../store/usePrefs";

/**
 * Dimensiona as células para o grid **preencher** o espaço disponível: a célula
 * é a maior que cabe na dimensão mais apertada (largura ÷ colunas vs altura ÷
 * linhas), então tudo aparece sem rolagem em retrato e paisagem e os botões
 * ocupam a tela em vez de ficarem espremidos no centro. O tamanho dos botões
 * passa a vir das colunas × linhas da página (configuráveis); o preset abaixo
 * só ajusta o espaçamento entre eles.
 */

const GAP: Record<GridSize, number> = { compact: 6, comfortable: 12, large: 20 };
const MIN_CELL = 40;
const MAX_CELL = 260; // evita botões gigantes em telas muito grandes (tablet)

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

  const gap = GAP[size];
  const fitW = box.w ? (box.w - (cols - 1) * gap) / cols : MAX_CELL;
  const fitH = box.h ? (box.h - (rows - 1) * gap) / rows : MAX_CELL;
  const cell = Math.max(MIN_CELL, Math.min(MAX_CELL, Math.floor(Math.min(fitW, fitH))));
  const width = cell * cols + gap * (cols - 1);

  return { ref, cell, gap, width };
}
