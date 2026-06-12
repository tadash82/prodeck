import { AnimatePresence, motion } from "motion/react";

import { useDeck } from "../store/useDeck";

export function Toast() {
  const toast = useDeck((s) => s.toast);
  return (
    <AnimatePresence>
      {toast && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 16 }}
          className="pointer-events-none fixed right-0 bottom-6 left-0 z-50 flex justify-center px-6"
        >
          <div
            className={`max-w-sm rounded-xl px-4 py-2.5 text-sm font-medium text-white shadow-lg ${
              toast.kind === "error" ? "bg-red-600" : "bg-green-600"
            }`}
          >
            {toast.text}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
