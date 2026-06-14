import { create } from "zustand";

/**
 * Preferências de exibição **locais do dispositivo** (tema, cor de destaque e
 * tamanho dos botões). Não fazem parte do protocolo/config do agente: são
 * estéticas e variam por aparelho (um tablet e um celular podem querer ajustes
 * diferentes), então vivem só no localStorage deste navegador.
 */

export type ThemeMode = "auto" | "light" | "dark";
export type GridSize = "compact" | "comfortable" | "large";

/** Cores de destaque oferecidas na UI (a `value` vira `--accent`). */
export const ACCENTS: { name: string; value: string }[] = [
  { name: "Azul", value: "#3b82f6" },
  { name: "Violeta", value: "#8b5cf6" },
  { name: "Rosa", value: "#ec4899" },
  { name: "Verde", value: "#22c55e" },
  { name: "Âmbar", value: "#f59e0b" },
  { name: "Ciano", value: "#06b6d4" },
];

type Prefs = { theme: ThemeMode; accent: string; size: GridSize };

const KEY = "prodeck:prefs";
const DEFAULTS: Prefs = { theme: "dark", accent: "#3b82f6", size: "comfortable" };

function load(): Prefs {
  try {
    return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(KEY) || "{}") };
  } catch {
    return { ...DEFAULTS };
  }
}

function persist(p: Prefs): void {
  try {
    localStorage.setItem(KEY, JSON.stringify({ theme: p.theme, accent: p.accent, size: p.size }));
  } catch {
    // localStorage indisponível (modo privado etc.): segue sem persistir.
  }
}

const prefersDark = () =>
  typeof matchMedia !== "undefined" && matchMedia("(prefers-color-scheme: dark)").matches;

/** Resolve "auto" e escreve o tema no DOM (data-theme + meta theme-color). */
function applyTheme(mode: ThemeMode): void {
  const dark = mode === "dark" || (mode === "auto" && prefersDark());
  document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
  document
    .querySelector('meta[name="theme-color"]')
    ?.setAttribute("content", dark ? "#0b1220" : "#eef2f7");
}

function applyAccent(accent: string): void {
  document.documentElement.style.setProperty("--accent", accent);
}

type PrefsState = Prefs & {
  setTheme: (theme: ThemeMode) => void;
  setAccent: (accent: string) => void;
  setSize: (size: GridSize) => void;
};

export const usePrefs = create<PrefsState>((set, get) => ({
  ...load(),
  setTheme: (theme) => {
    applyTheme(theme);
    set({ theme });
    persist(get());
  },
  setAccent: (accent) => {
    applyAccent(accent);
    set({ accent });
    persist(get());
  },
  setSize: (size) => {
    set({ size });
    persist(get());
  },
}));

/**
 * Aplica tema/accent atuais ao DOM e passa a reagir à troca de esquema do SO
 * quando o tema está em "auto". O index.html já fez a primeira aplicação (anti
 * flash); aqui só reforçamos e instalamos o listener.
 */
export function initPrefs(): void {
  const { theme, accent } = usePrefs.getState();
  applyTheme(theme);
  applyAccent(accent);
  if (typeof matchMedia !== "undefined") {
    matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
      if (usePrefs.getState().theme === "auto") applyTheme("auto");
    });
  }
}
