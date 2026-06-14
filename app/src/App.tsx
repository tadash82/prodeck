import { AnimatePresence } from "motion/react";

import { ConnectScreen } from "./components/ConnectScreen";
import { DeckGrid } from "./components/DeckGrid";
import { StatusBar } from "./components/StatusBar";
import { Toast } from "./components/Toast";
import { EditorSheet } from "./components/edit/EditorSheet";
import { ManageSheet } from "./components/edit/ManageSheet";
import { addPage } from "./lib/deckOps";
import { useDeck } from "./store/useDeck";

export default function App() {
  const status = useDeck((s) => s.status);
  const config = useDeck((s) => s.config);
  const activePageIndex = useDeck((s) => s.activePageIndex);
  const setPage = useDeck((s) => s.setPage);
  const editMode = useDeck((s) => s.editMode);
  const editTarget = useDeck((s) => s.editTarget);
  const manageOpen = useDeck((s) => s.manageOpen);
  const apply = useDeck((s) => s.apply);

  if (status !== "online" || !config) return <ConnectScreen status={status} />;

  const profiles = config.profiles ?? [];
  const profile = profiles.find((p) => p.id === config.active_profile) ?? profiles[0];
  const pages = profile?.pages ?? [];
  const page = pages[Math.min(activePageIndex, Math.max(pages.length - 1, 0))];

  if (!profile || !page) {
    return (
      <div className="flex min-h-full items-center justify-center p-8 text-center text-sm text-slate-400">
        Nenhum perfil configurado — toque no lápis para criar.
      </div>
    );
  }

  const addNewPage = () => {
    if (apply((c) => addPage(c, profile.id, ""))) setPage(pages.length);
  };

  return (
    <div className="safe-area flex h-dvh flex-col overflow-hidden">
      <StatusBar profileName={profile.name} />
      <main className="flex min-h-0 flex-1 items-center justify-center p-4">
        <DeckGrid page={page} profileId={profile.id} />
      </main>
      {(pages.length > 1 || editMode) && (
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
          {editMode && (
            <button
              onClick={addNewPage}
              aria-label="Nova página"
              className="flex h-5 w-5 items-center justify-center rounded-full bg-slate-800 text-xs text-slate-400 active:bg-slate-700"
            >
              +
            </button>
          )}
        </nav>
      )}

      <AnimatePresence>
        {editTarget && <EditorSheet key={`editor-${editTarget.kind}`} target={editTarget} />}
        {manageOpen && <ManageSheet key="manage" />}
      </AnimatePresence>
      <Toast />
    </div>
  );
}
