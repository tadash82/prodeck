import { Icon } from "@iconify/react";
import { useState } from "react";

import {
  addPage,
  addProfile,
  removePage,
  removeProfile,
  renamePage,
  renameProfile,
  setActiveProfile,
  setAllowShell,
} from "../../lib/deckOps";
import { useDeck } from "../../store/useDeck";
import { Appearance } from "./Appearance";
import { inputClass, Sheet } from "./Sheet";

type Renaming = { kind: "profile" | "page"; id: string; value: string };

export function ManageSheet() {
  const config = useDeck((s) => s.config);
  const apply = useDeck((s) => s.apply);
  const setManageOpen = useDeck((s) => s.setManageOpen);
  const setPage = useDeck((s) => s.setPage);

  const [renaming, setRenaming] = useState<Renaming | null>(null);
  const [armedDelete, setArmedDelete] = useState<string | null>(null);

  if (!config) return null;
  const profiles = config.profiles ?? [];
  const active = profiles.find((p) => p.id === config.active_profile) ?? profiles[0];

  const confirmRename = () => {
    if (!renaming) return;
    const { kind, id, value } = renaming;
    apply((c) =>
      kind === "profile" ? renameProfile(c, id, value) : renamePage(c, active.id, id, value),
    );
    setRenaming(null);
  };

  const rowButton = (
    onClick: () => void,
    icon: string,
    danger = false,
    armed = false,
  ) => (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-lg p-2 transition-colors ${
        armed
          ? "bg-red-600 text-white"
          : danger
            ? "text-red-400 active:bg-slate-700"
            : "text-slate-400 active:bg-slate-700"
      }`}
    >
      <Icon icon={armed ? "mdi:check" : icon} style={{ fontSize: "1rem" }} />
    </button>
  );

  const renderRow = (
    kind: Renaming["kind"],
    id: string,
    name: string,
    isActive: boolean,
    onActivate: (() => void) | null,
    onRemove: () => void,
  ) => {
    const key = `${kind}:${id}`;
    return (
      <div key={key} className="flex items-center gap-1 rounded-xl bg-slate-800/70 px-2 py-1.5">
        {renaming?.kind === kind && renaming.id === id ? (
          <>
            <input
              className={`${inputClass} py-1.5`}
              value={renaming.value}
              autoFocus
              onChange={(e) => setRenaming({ ...renaming, value: e.target.value })}
              onKeyDown={(e) => e.key === "Enter" && confirmRename()}
            />
            {rowButton(confirmRename, "mdi:check")}
          </>
        ) : (
          <>
            <button
              type="button"
              onClick={onActivate ?? undefined}
              disabled={!onActivate}
              className="flex flex-1 items-center gap-2 px-1 py-1 text-left text-sm text-slate-200"
            >
              <span
                className={`h-2 w-2 shrink-0 rounded-full ${
                  isActive ? "bg-blue-500" : "bg-slate-600"
                }`}
              />
              <span className="truncate">{name}</span>
            </button>
            {rowButton(() => setRenaming({ kind, id, value: name }), "mdi:pencil")}
            {rowButton(
              () => {
                if (armedDelete === key) {
                  setArmedDelete(null);
                  onRemove();
                } else {
                  setArmedDelete(key);
                }
              },
              "mdi:trash-can-outline",
              true,
              armedDelete === key,
            )}
          </>
        )}
      </div>
    );
  };

  return (
    <Sheet title="Perfis e páginas" onClose={() => setManageOpen(false)}>
      <div className="flex flex-col gap-5">
        <section className="flex flex-col gap-1.5">
          <h3 className="text-xs font-semibold tracking-wide text-slate-500 uppercase">
            Perfis
          </h3>
          {profiles.map((profile) =>
            renderRow(
              "profile",
              profile.id,
              profile.name,
              profile.id === config.active_profile,
              () => {
                apply((c) => setActiveProfile(c, profile.id));
                setPage(0);
              },
              () => apply((c) => removeProfile(c, profile.id)),
            ),
          )}
          <AddRow
            placeholder="Novo perfil…"
            onAdd={(name) => {
              apply((c) => addProfile(c, name));
              setPage(0);
            }}
          />
        </section>

        <section className="flex flex-col gap-1.5">
          <h3 className="text-xs font-semibold tracking-wide text-slate-500 uppercase">
            Páginas de “{active?.name}”
          </h3>
          {(active?.pages ?? []).map((page, index) =>
            renderRow(
              "page",
              page.id,
              page.name,
              false,
              () => {
                setPage(index);
                setManageOpen(false);
              },
              () => apply((c) => removePage(c, active.id, page.id)),
            ),
          )}
          <AddRow
            placeholder="Nova página…"
            onAdd={(name) => apply((c) => addPage(c, active.id, name))}
          />
        </section>

        <Appearance />

        <section className="flex flex-col gap-2">
          <h3 className="text-xs font-semibold tracking-wide text-slate-500 uppercase">
            Configurações
          </h3>
          <button
            type="button"
            onClick={() => apply((c) => setAllowShell(c, !(c.allow_shell ?? false)))}
            className="flex items-center justify-between rounded-xl bg-slate-800/70 px-3 py-2.5"
          >
            <span className="text-sm text-slate-200">Permitir ações shell</span>
            <span
              className={`flex h-6 w-11 items-center rounded-full px-0.5 transition-colors ${
                config.allow_shell ? "justify-end bg-amber-500" : "justify-start bg-slate-600"
              }`}
            >
              <span className="h-5 w-5 rounded-full bg-white shadow" />
            </span>
          </button>
          {config.allow_shell && (
            <p className="text-[11px] leading-relaxed text-amber-400">
              ⚠ Qualquer dispositivo pareado poderá executar comandos de shell neste
              PC. Toda execução fica registrada no log do agente.
            </p>
          )}
        </section>
      </div>
    </Sheet>
  );
}

function AddRow({ placeholder, onAdd }: { placeholder: string; onAdd: (name: string) => void }) {
  const [value, setValue] = useState("");
  const add = () => {
    onAdd(value);
    setValue("");
  };
  return (
    <div className="flex items-center gap-1.5">
      <input
        className={inputClass}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && add()}
        placeholder={placeholder}
      />
      <button
        type="button"
        onClick={add}
        className="rounded-xl bg-slate-800 p-2.5 text-slate-300 active:bg-slate-700"
      >
        <Icon icon="mdi:plus" style={{ fontSize: "1.1rem" }} />
      </button>
    </div>
  );
}
