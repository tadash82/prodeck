import { ConnectScreen } from "./components/ConnectScreen";
import { DeckGrid } from "./components/DeckGrid";
import { StatusBar } from "./components/StatusBar";
import { useDeck } from "./store/useDeck";

export default function App() {
  const status = useDeck((s) => s.status);
  const config = useDeck((s) => s.config);
  const activePageIndex = useDeck((s) => s.activePageIndex);
  const setPage = useDeck((s) => s.setPage);

  if (status !== "online" || !config) return <ConnectScreen status={status} />;

  const profiles = config.profiles ?? [];
  const profile =
    profiles.find((p) => p.id === config.active_profile) ?? profiles[0];
  const pages = profile?.pages ?? [];
  const page = pages[Math.min(activePageIndex, Math.max(pages.length - 1, 0))];

  if (!profile || !page) {
    return (
      <div className="flex min-h-full items-center justify-center p-8 text-center text-sm text-slate-400">
        Nenhum perfil configurado — edite o profiles.json no PC.
      </div>
    );
  }

  return (
    <div className="safe-area flex min-h-full flex-col">
      <StatusBar profileName={profile.name} />
      <main className="flex flex-1 items-center justify-center p-4">
        <DeckGrid page={page} />
      </main>
      {pages.length > 1 && (
        <nav className="flex items-center justify-center gap-3 pb-5">
          {pages.map((p, index) => (
            <button
              key={p.id}
              onClick={() => setPage(index)}
              aria-label={p.name}
              className={`h-2.5 rounded-full transition-all ${
                index === activePageIndex ? "w-6 bg-blue-500" : "w-2.5 bg-slate-700"
              }`}
            />
          ))}
        </nav>
      )}
    </div>
  );
}
