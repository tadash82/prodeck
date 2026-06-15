import { Icon } from "@iconify/react";
import { useEffect, useState } from "react";

import { token } from "../../lib/identity";
import type { Button } from "../../types/protocol";
import { labelClass } from "./Sheet";

export type MediaPreset = {
  label: string;
  icon: string;
  color: string;
  command: string[];
  state: Button["state"];
};

/** Atalhos prontos de áudio (mutar, volume) vindos do agente já com o comando
 * certo do backend (wpctl/pactl) — um toque preenche o botão. Some se a máquina
 * não tiver áudio detectável. */
export function MediaPresets({ onPick }: { onPick: (preset: MediaPreset) => void }) {
  const [presets, setPresets] = useState<MediaPreset[]>([]);

  useEffect(() => {
    fetch(`/audio?token=${encodeURIComponent(token() ?? "")}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((data: MediaPreset[]) => setPresets(data))
      .catch(() => setPresets([]));
  }, []);

  if (presets.length === 0) return null;

  return (
    <div>
      <label className={labelClass}>Atalhos de mídia</label>
      <div className="grid grid-cols-2 gap-1.5">
        {presets.map((preset) => (
          <button
            key={preset.label}
            type="button"
            onClick={() => onPick(preset)}
            className="flex items-center gap-2 rounded-xl bg-slate-800 px-3 py-2 text-sm font-medium text-slate-200 active:bg-slate-700"
          >
            <Icon icon={preset.icon} style={{ fontSize: "1.2rem", color: preset.color }} />
            {preset.label}
          </button>
        ))}
      </div>
    </div>
  );
}
