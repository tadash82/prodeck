import { Icon } from "@iconify/react";
import { useEffect, useMemo, useState } from "react";

import { token } from "../../lib/identity";
import { ButtonIcon } from "../ButtonIcon";
import { inputClass } from "./Sheet";

export type InstalledApp = { name: string; exec: string[]; icon: string | null };

/** Lista os apps instalados (via /apps no agente) para escolher um — preenche
 * o comando e o ícone do botão sem digitar nada. */
export function AppPicker({
  onPick,
  onClose,
}: {
  onPick: (app: InstalledApp) => void;
  onClose: () => void;
}) {
  const [apps, setApps] = useState<InstalledApp[] | null>(null);
  const [error, setError] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    fetch(`/apps?token=${encodeURIComponent(token() ?? "")}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((data: InstalledApp[]) => setApps(data))
      .catch(() => setError(true));
  }, []);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const list = apps ?? [];
    return needle ? list.filter((a) => a.name.toLowerCase().includes(needle)) : list;
  }, [apps, query]);

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-end">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className="relative flex max-h-[80vh] w-full max-w-lg flex-col rounded-t-3xl border-t border-slate-800 bg-slate-900 p-5">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-100">Escolher app instalado</h3>
          <button
            type="button"
            onClick={onClose}
            aria-label="Fechar"
            className="rounded-lg p-1 text-slate-400 active:bg-slate-800"
          >
            <Icon icon="mdi:close" style={{ fontSize: "1.2rem" }} />
          </button>
        </div>
        <input
          className={inputClass}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Buscar app…"
          autoFocus
        />
        <div className="mt-2 flex-1 overflow-y-auto">
          {error && (
            <p className="py-6 text-center text-sm text-slate-500">
              Não foi possível listar os apps deste PC.
            </p>
          )}
          {!apps && !error && (
            <p className="py-6 text-center text-sm text-slate-500">Carregando…</p>
          )}
          {filtered.map((app, index) => (
            <button
              key={`${app.name}-${index}`}
              type="button"
              onClick={() => onPick(app)}
              className="flex w-full items-center gap-3 rounded-xl px-2 py-2 text-left active:bg-slate-800"
            >
              <span className="flex h-8 w-8 shrink-0 items-center justify-center">
                {app.icon ? (
                  <ButtonIcon icon={app.icon} size="1.8rem" />
                ) : (
                  <Icon icon="mdi:application" style={{ fontSize: "1.5rem" }} className="text-slate-500" />
                )}
              </span>
              <span className="truncate text-sm text-slate-200">{app.name}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
