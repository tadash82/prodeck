import { AnimatePresence, motion } from "motion/react";
import { useState } from "react";

import { ConnectScreen } from "./components/ConnectScreen";
import { DeckGrid } from "./components/DeckGrid";
import { StatusBar } from "./components/StatusBar";
import { Toast } from "./components/Toast";
import { EditorSheet } from "./components/edit/EditorSheet";
import { ManageSheet } from "./components/edit/ManageSheet";
import { addPage } from "./lib/deckOps";
import { useDeck } from "./store/useDeck";

// Deslize entre páginas: `dir` é 1 (avança) ou -1 (volta), pra a página entrar
// pelo lado certo e a anterior sair pelo oposto.
const pageSlide = {
  enter: (dir: number) => ({ x: dir > 0 ? 80 : -80, opacity: 0 }),
  center: { x: 0, opacity: 1 },
  exit: (dir: number) => ({ x: dir > 0 ? -80 : 80, opacity: 0 }),
};

export default function App() {
  const status = useDeck((s) => s.status);
  const config = useDeck((s) => s.config);
  const activePageIndex = useDeck((s) => s.activePageIndex);
  const setPage = useDeck((s) => s.setPage);
  const editMode = useDeck((s) => s.editMode);
  const editTarget = useDeck((s) => s.editTarget);
  const manageOpen = useDeck((s) => s.manageOpen);
  const apply = useDeck((s) => s.apply);
  const [dir, setDir] = useState(0);

  if (status !== "online" || !config) return <ConnectScreen status={status} />;

  const profiles = config.profiles ?? [];
  const profile = profiles.find((p) => p.id === config.active_profile) ?? profiles[0];
  const pages = profile?.pages ?? [];
  const pageIndex = Math.min(activePageIndex, Math.max(pages.length - 1, 0));
  const page = pages[pageIndex];

  // Vai para uma página guardando a direção (pro deslize entrar pelo lado certo).
  const goToPage = (index: number) => {
    if (index < 0 || index >= pages.length || index === pageIndex) return;
    setDir(index > pageIndex ? 1 : -1);
    setPage(index);
  };

  if (!profile || !page) {
    return (
      <div className="flex min-h-full items-center justify-center p-8 text-center text-sm text-slate-400">
        Nenhum perfil configurado — toque no lápis para criar.
      </div>
    );
  }

  const addNewPage = () => {
    if (apply((c) => addPage(c, profile.id, ""))) {
      setDir(1);
      setPage(pages.length);
    }
  };

  return (
    <div className="safe-area flex h-dvh flex-col overflow-hidden">
      <StatusBar profileName={profile.name} />
      <motion.main
        className="relative min-h-0 flex-1 overflow-hidden"
        // pan-y: o navegador só cuida do scroll vertical; o arraste horizontal é
        // nosso (senão o gesto "voltar" da borda come o swipe pra direita).
        style={{ touchAction: "pan-y", overscrollBehaviorX: "contain" }}
        onPanEnd={(_, { offset, velocity }) => {
          // Em edição o arraste move botões; lá a troca é pelas bolinhas.
          if (editMode || pages.length < 2) return;
          if (Math.abs(offset.x) < Math.abs(offset.y)) return; // gesto vertical: ignora
          if (Math.abs(offset.x) < 60 && Math.abs(velocity.x) < 400) return;
          goToPage(pageIndex + (offset.x < 0 ? 1 : -1));
        }}
      >
        <AnimatePresence custom={dir} initial={false}>
          <motion.div
            key={page.id}
            custom={dir}
            variants={pageSlide}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ type: "spring", stiffness: 360, damping: 34 }}
            className="absolute inset-0 flex items-center justify-center p-4"
          >
            <DeckGrid page={page} profileId={profile.id} />
          </motion.div>
        </AnimatePresence>
      </motion.main>
      {(pages.length > 1 || editMode) && (
        <nav className="flex items-center justify-center gap-3 pb-5">
          {pages.map((p, index) => (
            <button
              key={p.id}
              onClick={() => goToPage(index)}
              aria-label={p.name}
              className={`h-2.5 rounded-full transition-all ${
                index === pageIndex ? "w-6 bg-blue-500" : "w-2.5 bg-slate-700"
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
