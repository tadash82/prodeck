import { useDraggable } from "@dnd-kit/core";
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
};

export function DeckButton({ button, profileId, pageId }: DeckButtonProps) {
  const trigger = useDeck((s) => s.trigger);
  const editMode = useDeck((s) => s.editMode);
  const setEditMode = useDeck((s) => s.setEditMode);
  const openEditor = useDeck((s) => s.openEditor);
  const result = useDeck((s) => s.results[button.id]);
  const active = useDeck((s) => s.buttonStates[button.id] ?? false);
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

  const color = button.color ?? FALLBACK_COLOR;
  const ring =
    flash !== null
      ? flash.status === "ok"
        ? ", 0 0 0 3px #22c55e"
        : ", 0 0 0 3px #ef4444"
      : active
        ? ", 0 0 0 2.5px #ffffffe6"
        : "";

  const onClick = () => {
    if (longPress.firedRecently() || Date.now() - lastDragEndAt < 200) return;
    if (editMode) edit();
    else trigger(button.id);
  };

  return (
    <motion.button
      ref={setNodeRef}
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
      <ButtonIcon icon={button.icon ?? FALLBACK_ICON} size="2.1rem" />
      <span className="px-1 text-center text-[11px] leading-tight font-semibold text-white/90">
        {button.label}
      </span>
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
