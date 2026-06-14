import { Icon } from "@iconify/react";
import type { ReactNode } from "react";

import { ACCENTS, usePrefs, type GridSize, type ThemeMode } from "../../store/usePrefs";

const THEMES: { value: ThemeMode; label: string; icon: string }[] = [
  { value: "auto", label: "Auto", icon: "mdi:theme-light-dark" },
  { value: "light", label: "Claro", icon: "mdi:white-balance-sunny" },
  { value: "dark", label: "Escuro", icon: "mdi:weather-night" },
];

const SIZES: { value: GridSize; label: string }[] = [
  { value: "compact", label: "Compacto" },
  { value: "comfortable", label: "Confortável" },
  { value: "large", label: "Grande" },
];

const subLabel = "mb-1.5 block text-xs font-medium text-slate-400";

/** Seção "Aparência" do gerenciador: tema, cor de destaque e tamanho dos botões. */
export function Appearance() {
  const theme = usePrefs((s) => s.theme);
  const accent = usePrefs((s) => s.accent);
  const size = usePrefs((s) => s.size);
  const setTheme = usePrefs((s) => s.setTheme);
  const setAccent = usePrefs((s) => s.setAccent);
  const setSize = usePrefs((s) => s.setSize);

  return (
    <section className="flex flex-col gap-3">
      <h3 className="text-xs font-semibold tracking-wide text-slate-500 uppercase">Aparência</h3>

      <div>
        <span className={subLabel}>Tema</span>
        <div className="grid grid-cols-3 gap-1.5">
          {THEMES.map((t) => (
            <Segment key={t.value} active={theme === t.value} onClick={() => setTheme(t.value)}>
              <Icon icon={t.icon} style={{ fontSize: "1.05rem" }} />
              {t.label}
            </Segment>
          ))}
        </div>
      </div>

      <div>
        <span className={subLabel}>Cor de destaque</span>
        <div className="flex flex-wrap gap-2">
          {ACCENTS.map((a) => (
            <button
              key={a.value}
              type="button"
              aria-label={a.name}
              onClick={() => setAccent(a.value)}
              className={`h-8 w-8 rounded-full transition-transform ${
                a.value === accent ? "scale-110 ring-2 ring-slate-100" : "active:scale-95"
              }`}
              style={{ background: a.value }}
            />
          ))}
        </div>
      </div>

      <div>
        <span className={subLabel}>Tamanho dos botões</span>
        <div className="grid grid-cols-3 gap-1.5">
          {SIZES.map((s) => (
            <Segment key={s.value} active={size === s.value} onClick={() => setSize(s.value)}>
              {s.label}
            </Segment>
          ))}
        </div>
      </div>
    </section>
  );
}

function Segment({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex items-center justify-center gap-1.5 rounded-xl px-2 py-2 text-xs font-medium transition-colors ${
        active ? "bg-blue-600 text-white" : "bg-slate-800/70 text-slate-300 active:bg-slate-700"
      }`}
    >
      {children}
    </button>
  );
}
