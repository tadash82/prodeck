import { Icon } from "@iconify/react";
import { motion } from "motion/react";
import { useEffect, useState } from "react";

import { useDeck, type ButtonResult } from "../store/useDeck";
import type { Button } from "../types/protocol";

const FALLBACK_COLOR = "#3b82f6";
const FALLBACK_ICON = "mdi:gesture-tap-button";

export function DeckButton({ button }: { button: Button }) {
  const trigger = useDeck((s) => s.trigger);
  const result = useDeck((s) => s.results[button.id]);
  const [flash, setFlash] = useState<ButtonResult | null>(null);

  useEffect(() => {
    if (!result) return;
    setFlash(result);
    const timer = setTimeout(() => setFlash(null), 900);
    return () => clearTimeout(timer);
  }, [result]);

  const color = button.color ?? FALLBACK_COLOR;
  const ring =
    flash === null
      ? ""
      : flash.status === "ok"
        ? ", 0 0 0 3px #22c55e"
        : ", 0 0 0 3px #ef4444";

  return (
    <motion.button
      whileTap={{ scale: 0.92 }}
      animate={flash?.status === "error" ? { x: [0, -6, 6, -4, 0] } : { x: 0 }}
      transition={{ duration: 0.35 }}
      onClick={() => trigger(button.id)}
      title={flash?.status === "error" ? flash.message : undefined}
      className="flex aspect-square flex-col items-center justify-center gap-1.5 overflow-hidden rounded-2xl text-white"
      style={{
        gridColumnStart: button.position.col + 1,
        gridRowStart: button.position.row + 1,
        background: `linear-gradient(160deg, ${color}, color-mix(in srgb, ${color} 55%, #000))`,
        boxShadow: `0 10px 24px -12px ${color}${ring}`,
      }}
    >
      <Icon icon={button.icon ?? FALLBACK_ICON} style={{ fontSize: "2.1rem" }} />
      <span className="px-1 text-center text-[11px] leading-tight font-semibold text-white/90">
        {button.label}
      </span>
    </motion.button>
  );
}
