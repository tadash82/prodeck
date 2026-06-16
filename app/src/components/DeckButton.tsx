import { useDraggable, useDroppable } from "@dnd-kit/core";
import { Icon } from "@iconify/react";
import { motion } from "motion/react";
import { useEffect, useState } from "react";

import { useLongPress } from "../lib/useLongPress";
import { useDeck, type ButtonResult } from "../store/useDeck";
import type { Button } from "../types/protocol";
import { ButtonIcon } from "./ButtonIcon";

const FALLBACK_COLOR = "#3b82f6";
const FALLBACK_ICON = "mdi:gesture-tap-button";

// clique fantasma que o navegador dispara logo após um drag deve ser ignorado
let lastDragEndAt = 0;
export function markDragEnd(): void {
  lastDragEndAt = Date.now();
}

type DeckButtonProps = {
  button: Button;
  profileId: string;
  pageId: string;
  cell: number;
};

export function DeckButton({ button, profileId, pageId, cell }: DeckButtonProps) {
  const trigger = useDeck((s) => s.trigger);
  const editMode = useDeck((s) => s.editMode);
  const setEditMode = useDeck((s) => s.setEditMode);
  const openEditor = useDeck((s) => s.openEditor);
  const result = useDeck((s) => s.results[button.id]);
  const active = useDeck((s) => s.buttonStates[button.id] ?? false);
  const widgetValue = useDeck((s) => s.widgetValues[button.id]);
  const [flash, setFlash] = useState<ButtonResult | null>(null);

  useEffect(() => {
    if (!result) return;
    setFlash(result);
    const timer = setTimeout(() => setFlash(null), 900);
    return () => clearTimeout(timer);
  }, [result]);

  const edit = () => openEditor({ kind: "edit", profileId, pageId, button });
  const longPress = useLongPress(() => {
    setEditMode(true);
    edit();
  });

  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: button.id,
    disabled: !editMode,
  });
  // a própria célula também é alvo de drop: arrastar um botão sobre outro troca
  // as posições (moveButton). Sem isto, só dava para soltar em célula vazia.
  const { setNodeRef: setDropRef, isOver } = useDroppable({
    id: `cell-${button.position.col}-${button.position.row}`,
    disabled: !editMode,
  });
  const setRefs = (node: HTMLElement | null) => {
    setNodeRef(node);
    setDropRef(node);
  };

  // ícone proporcional à célula (cell px) — fixo ficava minúsculo em telas grandes
  const iconSize = button.widget
    ? `${Math.round(cell * 0.24)}px`
    : `${Math.round(cell * 0.42)}px`;

  const color = button.color ?? FALLBACK_COLOR;
  const ring =
    isOver && !isDragging
      ? ", 0 0 0 3px #3b82f6"
      : flash !== null
        ? flash.status === "ok"
          ? ", 0 0 0 3px #22c55e"
          : ", 0 0 0 3px #ef4444"
        : active
          ? ", 0 0 0 2.5px #ffffffe6"
          : "";

  const onClick = () => {
    if (longPress.firedRecently() || Date.now() - lastDragEndAt < 200) return;
    if (editMode) edit();
    else if (button.action) trigger(button.id); // botão só-widget não dispara nada
  };

  return (
    <motion.button
      ref={setRefs}
      whileTap={isDragging ? undefined : { scale: 0.92 }}
      animate={
        flash?.status === "error"
          ? { x: [0, -6, 6, -4, 0] }
          : editMode && !isDragging
            ? { rotate: [0, -0.7, 0.7, 0], transition: { repeat: Infinity, duration: 0.45 } }
            : { x: 0, rotate: 0 }
      }
      transition={{ duration: 0.35 }}
      onClick={onClick}
      title={flash?.status === "error" ? flash.message : undefined}
      className="relative flex aspect-square touch-none flex-col items-center justify-center gap-1.5 overflow-hidden rounded-2xl text-white"
      style={{
        gridColumnStart: button.position.col + 1,
        gridRowStart: button.position.row + 1,
        background: `linear-gradient(160deg, ${color}, color-mix(in srgb, ${color} 55%, #000))`,
        boxShadow: `0 10px 24px -12px ${color}${ring}`,
        transform: transform
          ? `translate3d(${transform.x}px, ${transform.y}px, 0) scale(1.06)`
          : undefined,
        zIndex: isDragging ? 30 : undefined,
        opacity: isDragging ? 0.9 : 1,
      }}
      {...(editMode ? { ...attributes, ...listeners } : longPress.handlers)}
    >
      {button.widget ? (
        <>
          <ButtonIcon icon={button.icon ?? FALLBACK_ICON} size={iconSize} />
          <span
            className={`font-bold leading-none tabular-nums ${
              (widgetValue ?? "").length <= 6 ? "text-xl" : "text-sm"
            }`}
          >
            {widgetValue ?? "…"}
          </span>
          <span className="px-1 text-center text-[10px] leading-tight text-white/75">
            {button.label}
          </span>
        </>
      ) : (
        <>
          <ButtonIcon icon={button.icon ?? FALLBACK_ICON} size={iconSize} />
          {button.label && (
            <span
              className="px-1 text-center leading-tight font-semibold text-white/90"
              style={{ fontSize: `${Math.max(11, Math.round(cell * 0.13))}px` }}
            >
              {button.label}
            </span>
          )}
        </>
      )}
      {editMode && (
        <span className="absolute top-1.5 right-1.5 rounded-full bg-black/30 p-1">
          <Icon icon="mdi:pencil" style={{ fontSize: "0.75rem" }} />
        </span>
      )}
      {active && !editMode && (
        <span className="absolute top-1.5 left-1.5 h-2 w-2 rounded-full bg-white shadow-[0_0_6px_#fff]" />
      )}
    </motion.button>
  );
}
