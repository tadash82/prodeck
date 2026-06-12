import { Icon } from "@iconify/react";

import type { Steps } from "../../types/protocol";

export type MacroStep = Steps[number];
export type StepType = NonNullable<MacroStep["type"]>;
export type StepForm = { type: StepType; value: string };

const STEP_LABEL: Record<StepType, string> = {
  open_app: "Programa",
  open_path: "Pasta",
  open_url: "URL",
  hotkey: "Atalho",
  text: "Texto",
  shell: "Shell",
  delay: "Espera",
};

const PLACEHOLDER: Record<StepType, string> = {
  open_app: "code-insiders ~/Projetos/MeuApp",
  open_path: "~/Downloads",
  open_url: "https://github.com",
  hotkey: "ctrl+alt+t",
  text: "texto a digitar",
  shell: "docker compose up -d",
  delay: "500 (ms)",
};

export function buildStep(step: StepForm): MacroStep | null {
  const value = step.value.trim();
  switch (step.type) {
    case "open_app": {
      const parts = value.split(/\s+/).filter(Boolean);
      return parts.length
        ? { type: "open_app", command: parts as [string, ...string[]] }
        : null;
    }
    case "open_path":
      return value ? { type: "open_path", path: value } : null;
    case "open_url":
      return /^https?:\/\//.test(value) ? { type: "open_url", url: value } : null;
    case "hotkey": {
      const keys = value
        .split("+")
        .map((s) => s.trim().toLowerCase())
        .filter(Boolean);
      return keys.length ? { type: "hotkey", keys: keys as [string, ...string[]] } : null;
    }
    case "text":
      return value ? { type: "text", text: value } : null;
    case "shell":
      return value ? { type: "shell", command: value } : null;
    case "delay": {
      const ms = Number(value);
      return Number.isInteger(ms) && ms >= 0 && ms <= 30000
        ? { type: "delay", ms }
        : null;
    }
    default:
      return null;
  }
}

export function stepToForm(step: MacroStep): StepForm {
  switch (step.type) {
    case "open_app":
      return { type: "open_app", value: step.command.join(" ") };
    case "open_path":
      return { type: "open_path", value: step.path };
    case "open_url":
      return { type: "open_url", value: step.url };
    case "hotkey":
      return { type: "hotkey", value: step.keys.join("+") };
    case "text":
      return { type: "text", value: step.text };
    case "shell":
      return { type: "shell", value: step.command };
    case "delay":
      return { type: "delay", value: String(step.ms) };
    default:
      return { type: "open_app", value: "" };
  }
}

export function MacroBuilder({
  steps,
  onChange,
}: {
  steps: StepForm[];
  onChange: (steps: StepForm[]) => void;
}) {
  const update = (index: number, patch: Partial<StepForm>) =>
    onChange(steps.map((s, i) => (i === index ? { ...s, ...patch } : s)));
  const move = (index: number, delta: number) => {
    const target = index + delta;
    if (target < 0 || target >= steps.length) return;
    const copy = [...steps];
    [copy[index], copy[target]] = [copy[target], copy[index]];
    onChange(copy);
  };

  const tinyButton = (onClick: () => void, icon: string, disabled = false) => (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="rounded-md p-1.5 text-slate-400 active:bg-slate-700 disabled:opacity-30"
    >
      <Icon icon={icon} style={{ fontSize: "0.85rem" }} />
    </button>
  );

  return (
    <div className="flex flex-col gap-2">
      {steps.map((step, index) => (
        <div key={index} className="flex items-center gap-1">
          <span className="w-4 text-center text-[10px] text-slate-500">{index + 1}</span>
          <select
            value={step.type}
            onChange={(e) => update(index, { type: e.target.value as StepType, value: step.value })}
            className="rounded-lg border border-slate-700 bg-slate-800 px-1.5 py-2 text-xs text-slate-200"
          >
            {Object.entries(STEP_LABEL).map(([type, label]) => (
              <option key={type} value={type}>
                {label}
              </option>
            ))}
          </select>
          <input
            className={`min-w-0 flex-1 rounded-lg border bg-slate-800 px-2 py-2 font-mono text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none ${
              buildStep(step) === null ? "border-red-500/70" : "border-slate-700"
            }`}
            value={step.value}
            onChange={(e) => update(index, { value: e.target.value })}
            placeholder={PLACEHOLDER[step.type]}
          />
          {tinyButton(() => move(index, -1), "mdi:arrow-up", index === 0)}
          {tinyButton(() => move(index, 1), "mdi:arrow-down", index === steps.length - 1)}
          {tinyButton(() => onChange(steps.filter((_, i) => i !== index)), "mdi:close")}
        </div>
      ))}
      <button
        type="button"
        onClick={() => onChange([...steps, { type: "open_app", value: "" }])}
        className="flex items-center justify-center gap-1 rounded-xl border border-dashed border-slate-700 py-2 text-xs font-medium text-slate-400 active:bg-slate-800"
      >
        <Icon icon="mdi:plus" /> adicionar passo
      </button>
    </div>
  );
}
