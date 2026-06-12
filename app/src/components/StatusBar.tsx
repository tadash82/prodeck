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
  return (
    <header className="flex items-center justify-between px-4 py-3 text-slate-400">
      <span className="text-sm font-semibold text-slate-200">{profileName}</span>
      <span className="flex items-center gap-2 text-xs tabular-nums">
        {status === "online" && rttMs !== null && <span>{rttMs} ms</span>}
        <span className={`h-2 w-2 rounded-full ${DOT[status] ?? "bg-slate-500"}`} />
      </span>
    </header>
  );
}
