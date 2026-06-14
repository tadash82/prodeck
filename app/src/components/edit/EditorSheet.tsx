import { Icon } from "@iconify/react";
import { useState } from "react";
import { createPortal } from "react-dom";

import { newId, removeButton, upsertButton } from "../../lib/deckOps";
import { useDeck, type EditTarget } from "../../store/useDeck";
import type { Action, Button } from "../../types/protocol";
import { ButtonIcon } from "../ButtonIcon";
import { AppPicker, type InstalledApp } from "./AppPicker";
import { ColorPicker } from "./ColorPicker";
import { IconPicker } from "./IconPicker";
import { MacroBuilder, buildStep, stepToForm, type MacroStep, type StepForm } from "./MacroBuilder";
import { inputClass, labelClass, Sheet } from "./Sheet";

type ActionType = Action["type"];

const ACTION_TABS: { type: ActionType; label: string; icon: string }[] = [
  { type: "open_app", label: "Programa", icon: "mdi:application-outline" },
  { type: "open_path", label: "Pasta", icon: "mdi:folder-outline" },
  { type: "open_url", label: "URL", icon: "mdi:web" },
  { type: "hotkey", label: "Atalho", icon: "mdi:keyboard-outline" },
  { type: "text", label: "Texto", icon: "mdi:form-textbox" },
  { type: "shell", label: "Shell", icon: "mdi:console-line" },
  { type: "macro", label: "Macro", icon: "mdi:playlist-play" },
];

export function EditorSheet({ target }: { target: EditTarget }) {
  const apply = useDeck((s) => s.apply);
  const closeEditor = useDeck((s) => s.closeEditor);

  const existing = target.kind === "edit" ? target.button : null;
  const action = existing?.action ?? null;
  const initCommand = action?.type === "open_app" ? action.command : [];

  const [label, setLabel] = useState(existing?.label ?? "");
  const [icon, setIcon] = useState(existing?.icon ?? "mdi:gesture-tap-button");
  const [color, setColor] = useState(existing?.color ?? "#3b82f6");
  const [actionType, setActionType] = useState<ActionType>(action?.type ?? "open_app");
  const [program, setProgram] = useState(initCommand[0] ?? "");
  const [args, setArgs] = useState(initCommand.slice(1).join("\n"));
  const [appPickerOpen, setAppPickerOpen] = useState(false);
  const [path, setPath] = useState(action?.type === "open_path" ? action.path : "");
  const [url, setUrl] = useState(action?.type === "open_url" ? action.url : "");
  const [keys, setKeys] = useState(action?.type === "hotkey" ? action.keys.join("+") : "");
  const [text, setText] = useState(action?.type === "text" ? action.text : "");
  const [shellCmd, setShellCmd] = useState(action?.type === "shell" ? action.command : "");
  const [macroSteps, setMacroSteps] = useState<StepForm[]>(
    action?.type === "macro" ? action.steps.map(stepToForm) : [],
  );
  const [stateSel, setStateSel] = useState<string>(existing?.state ?? "");
  const [confirmDelete, setConfirmDelete] = useState(false);

  function buildAction(): Action | null {
    switch (actionType) {
      case "open_app": {
        const prog = program.trim();
        if (!prog) return null;
        const extra = args
          .split("\n")
          .map((s) => s.trim())
          .filter(Boolean);
        return { type: "open_app", command: [prog, ...extra] as [string, ...string[]] };
      }
      case "open_path": {
        const p = path.trim();
        return p ? { type: "open_path", path: p } : null;
      }
      case "open_url": {
        const u = url.trim();
        return /^https?:\/\//.test(u) ? { type: "open_url", url: u } : null;
      }
      case "hotkey": {
        const parsed = keys
          .split("+")
          .map((s) => s.trim().toLowerCase())
          .filter(Boolean);
        return parsed.length
          ? { type: "hotkey", keys: parsed as [string, ...string[]] }
          : null;
      }
      case "text": {
        return text.trim() ? { type: "text", text } : null;
      }
      case "shell": {
        const c = shellCmd.trim();
        return c ? { type: "shell", command: c } : null;
      }
      case "macro": {
        if (macroSteps.length === 0) return null;
        const built = macroSteps.map(buildStep);
        if (built.some((s) => s === null)) return null;
        return { type: "macro", steps: built as MacroStep[] as [MacroStep, ...MacroStep[]] };
      }
      default:
        return null;
    }
  }

  const builtAction = buildAction();
  const valid = label.trim().length > 0 && builtAction !== null;

  const pickApp = (app: InstalledApp) => {
    setProgram(app.exec[0] ?? "");
    setArgs(app.exec.slice(1).join("\n"));
    if (app.icon) setIcon(app.icon);
    if (!label.trim()) setLabel(app.name);
    setAppPickerOpen(false);
  };

  const save = () => {
    if (!builtAction) return;
    const button: Button = {
      id: existing?.id ?? newId("btn"),
      position:
        existing?.position ?? (target.kind === "new" ? target.position : { col: 0, row: 0 }),
      label: label.trim(),
      icon,
      color,
      action: builtAction,
      state: stateSel === "" ? null : (stateSel as Button["state"]),
    };
    if (apply((c) => upsertButton(c, target.profileId, target.pageId, button))) {
      closeEditor();
    }
  };

  const remove = () => {
    if (!existing) return;
    if (!confirmDelete) {
      setConfirmDelete(true);
      return;
    }
    if (apply((c) => removeButton(c, target.profileId, target.pageId, existing.id))) {
      closeEditor();
    }
  };

  return (
    <Sheet title={existing ? "Editar botão" : "Novo botão"} onClose={closeEditor}>
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <div
            className="flex h-20 w-20 shrink-0 flex-col items-center justify-center gap-1 rounded-2xl text-white"
            style={{
              background: `linear-gradient(160deg, ${color}, color-mix(in srgb, ${color} 55%, #000))`,
            }}
          >
            <ButtonIcon icon={icon} size="2rem" />
            <span className="max-w-16 truncate px-1 text-[9px] font-semibold">
              {label.trim() || "Botão"}
            </span>
          </div>
          <div className="flex-1">
            <label className={labelClass}>Nome</label>
            <input
              className={inputClass}
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="ex.: VSCode · Projeto"
            />
          </div>
        </div>

        <div>
          <label className={labelClass}>Ação</label>
          <div className="grid grid-cols-4 gap-1.5">
            {ACTION_TABS.map((tab) => (
              <button
                key={tab.type}
                type="button"
                onClick={() => setActionType(tab.type)}
                className={`flex flex-col items-center gap-1 rounded-xl px-1 py-2 text-[11px] font-medium transition-colors ${
                  actionType === tab.type
                    ? "bg-blue-600 text-white"
                    : "bg-slate-800 text-slate-300 active:bg-slate-700"
                }`}
              >
                <Icon icon={tab.icon} style={{ fontSize: "1.15rem" }} />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {actionType === "open_app" && (
          <div className="flex flex-col gap-2">
            <button
              type="button"
              onClick={() => setAppPickerOpen(true)}
              className="flex items-center justify-center gap-2 rounded-xl bg-slate-800 px-3 py-2.5 text-sm font-medium text-slate-200 active:bg-slate-700"
            >
              <Icon icon="mdi:apps" style={{ fontSize: "1.2rem" }} />
              Escolher app instalado
            </button>
            <div>
              <label className={labelClass}>Programa</label>
              <input
                className={`${inputClass} font-mono`}
                value={program}
                onChange={(e) => setProgram(e.target.value)}
                placeholder="code-insiders"
              />
            </div>
            <div>
              <label className={labelClass}>Argumentos — um por linha (opcional)</label>
              <textarea
                className={`${inputClass} min-h-16 font-mono`}
                value={args}
                onChange={(e) => setArgs(e.target.value)}
                placeholder="/home/voce/Projetos/MeuApp"
              />
            </div>
          </div>
        )}
        {actionType === "open_path" && (
          <div>
            <label className={labelClass}>Caminho da pasta ou arquivo</label>
            <input
              className={`${inputClass} font-mono`}
              value={path}
              onChange={(e) => setPath(e.target.value)}
              placeholder="~/Downloads"
            />
          </div>
        )}
        {actionType === "open_url" && (
          <div>
            <label className={labelClass}>URL</label>
            <input
              className={`${inputClass} font-mono`}
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://github.com"
              inputMode="url"
            />
            {url.trim() !== "" && builtAction === null && (
              <p className="mt-1 text-[11px] text-amber-400">
                Precisa começar com http:// ou https://
              </p>
            )}
          </div>
        )}
        {actionType === "hotkey" && (
          <div>
            <label className={labelClass}>Teclas — junte com +</label>
            <input
              className={`${inputClass} font-mono`}
              value={keys}
              onChange={(e) => setKeys(e.target.value)}
              placeholder="ctrl+alt+t"
            />
            <p className="mt-1 text-[11px] text-slate-500">
              Modificadores: ctrl, alt, shift, super. Ex.: super+l, ctrl+shift+m, f5
            </p>
          </div>
        )}
        {actionType === "text" && (
          <div>
            <label className={labelClass}>Texto a digitar</label>
            <textarea
              className={`${inputClass} min-h-20`}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Será digitado onde o cursor estiver no PC"
            />
          </div>
        )}
        {actionType === "shell" && (
          <div>
            <label className={labelClass}>Comando de shell</label>
            <textarea
              className={`${inputClass} min-h-20 font-mono`}
              value={shellCmd}
              onChange={(e) => setShellCmd(e.target.value)}
              placeholder="docker compose up -d"
            />
            <p className="mt-1 text-[11px] text-amber-400">
              ⚠ Roda no shell do PC com seus privilégios. Exige “Permitir ações shell”
              em Perfis e páginas.
            </p>
          </div>
        )}
        {actionType === "macro" && (
          <div>
            <label className={labelClass}>Passos da sequência</label>
            <MacroBuilder steps={macroSteps} onChange={setMacroSteps} />
          </div>
        )}

        <IconPicker value={icon} onChange={setIcon} />
        <ColorPicker value={color} onChange={setColor} />

        <div>
          <label className={labelClass}>Indicador de estado (opcional)</label>
          <select
            className={inputClass}
            value={stateSel}
            onChange={(e) => setStateSel(e.target.value)}
          >
            <option value="">Nenhum</option>
            <option value="mic_muted">Microfone mutado</option>
            <option value="audio_muted">Áudio mutado</option>
          </select>
          <p className="mt-1 text-[11px] text-slate-500">
            O botão acende quando o estado estiver ativo no PC.
          </p>
        </div>

        <div className="mt-1 flex items-center gap-2">
          {existing && (
            <button
              type="button"
              onClick={remove}
              className={`rounded-xl px-4 py-2.5 text-sm font-semibold transition-colors ${
                confirmDelete
                  ? "bg-red-600 text-white"
                  : "bg-slate-800 text-red-400 active:bg-slate-700"
              }`}
            >
              {confirmDelete ? "Confirmar?" : "Excluir"}
            </button>
          )}
          <div className="flex-1" />
          <button
            type="button"
            onClick={closeEditor}
            className="rounded-xl bg-slate-800 px-4 py-2.5 text-sm font-semibold text-slate-300 active:bg-slate-700"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={save}
            disabled={!valid}
            className="rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white active:bg-blue-500 disabled:opacity-40"
          >
            Salvar
          </button>
        </div>
      </div>
      {appPickerOpen &&
        createPortal(
          <AppPicker onPick={pickApp} onClose={() => setAppPickerOpen(false)} />,
          document.body,
        )}
    </Sheet>
  );
}
