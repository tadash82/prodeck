import { Icon } from "@iconify/react";

import { useDeck } from "../store/useDeck";

const DOT: Record<string, string> = {
  online: "bg-green-500 shadow-[0_0_8px_#22c55e88]",
  connecting: "bg-amber-400 animate-pulse",
  offline: "bg-red-500 animate-pulse",
  denied: "bg-red-500",
  "no-token": "bg-slate-500",
};

export function StatusBar({ profileName }: { profileName: string }) {
  const status = useDeck((s) => s.status);
  const rttMs = useDeck((s) => s.rttMs);
  const editMode = useDeck((s) => s.editMode);
  const setEditMode = useDeck((s) => s.setEditMode);
  const setManageOpen = useDeck((s) => s.setManageOpen);

  return (
    <header className="flex items-center justify-between px-4 py-3 text-slate-400">
      <span className="flex items-center gap-2 text-sm font-semibold text-slate-200">
        {profileName}
        {editMode && (
          <span className="rounded-full bg-blue-600/20 px-2 py-0.5 text-[10px] font-semibold text-blue-400">
            editando
          </span>
        )}
      </span>
      <span className="flex items-center gap-1.5">
        {editMode && (
          <button
            type="button"
            onClick={() => setManageOpen(true)}
            aria-label="Perfis e páginas"
            className="rounded-lg p-2 text-slate-300 active:bg-slate-800"
          >
            <Icon icon="mdi:folder-cog-outline" style={{ fontSize: "1.15rem" }} />
          </button>
        )}
        <button
          type="button"
          onClick={() => setEditMode(!editMode)}
          aria-label={editMode ? "Concluir edição" : "Editar deck"}
          className={`rounded-lg p-2 transition-colors ${
            editMode ? "bg-blue-600 text-white" : "text-slate-300 active:bg-slate-800"
          }`}
        >
          <Icon
            icon={editMode ? "mdi:check" : "mdi:pencil-outline"}
            style={{ fontSize: "1.15rem" }}
          />
        </button>
        <span className="ml-1 flex items-center gap-2 text-xs tabular-nums">
          {status === "online" && rttMs !== null && <span>{rttMs} ms</span>}
          <span className={`h-2 w-2 rounded-full ${DOT[status] ?? "bg-slate-500"}`} />
        </span>
      </span>
    </header>
  );
}
