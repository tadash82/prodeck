import { Icon } from "@iconify/react";
import { useEffect, useState } from "react";

import { token } from "../../lib/identity";
import type { Button } from "../../types/protocol";
import { labelClass } from "./Sheet";

export type QuickAction = {
  label: string;
  icon: string;
  color: string;
  command: string[];
  state: Button["state"];
};

/** Atalhos prontos vindos do agente (mídia e sistema) já com o comando certo da
 * máquina — wpctl/pactl pra som, loginctl pra bloquear etc. Um toque preenche o
 * botão inteiro, sem o usuário precisar saber qual comando usar. Some se a
 * máquina não suportar nenhum. */
export function QuickActions({ onPick }: { onPick: (action: QuickAction) => void }) {
  const [actions, setActions] = useState<QuickAction[]>([]);

  useEffect(() => {
    fetch(`/presets?token=${encodeURIComponent(token() ?? "")}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((data: QuickAction[]) => setActions(data))
      .catch(() => setActions([]));
  }, []);

  if (actions.length === 0) return null;

  return (
    <div>
      <label className={labelClass}>Atalhos prontos</label>
      <div className="grid grid-cols-2 gap-1.5">
        {actions.map((action) => (
          <button
            key={action.label}
            type="button"
            onClick={() => onPick(action)}
            className="flex items-center gap-2 rounded-xl bg-slate-800 px-3 py-2 text-sm font-medium text-slate-200 active:bg-slate-700"
          >
            <Icon icon={action.icon} style={{ fontSize: "1.2rem", color: action.color }} />
            {action.label}
          </button>
        ))}
      </div>
    </div>
  );
}
