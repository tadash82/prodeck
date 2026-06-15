import { Icon } from "@iconify/react";
import { useRef, useState, type ChangeEvent } from "react";

import {
  addAutoRule,
  addPage,
  addProfile,
  exportProfile,
  GRID_LIMITS,
  importProfiles,
  removeAutoRule,
  removePage,
  removeProfile,
  renamePage,
  renameProfile,
  repackButtons,
  setActiveProfile,
  setAllowShell,
  setGrid,
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
  const activePageIndex = useDeck((s) => s.activePageIndex);
  const showToast = useDeck((s) => s.showToast);

  const [renaming, setRenaming] = useState<Renaming | null>(null);
  const [armedDelete, setArmedDelete] = useState<string | null>(null);
  const importRef = useRef<HTMLInputElement>(null);

  const doExport = (profileId: string) => {
    try {
      const { filename, json } = exportProfile(config!, profileId);
      const url = URL.createObjectURL(new Blob([json], { type: "application/json" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      showToast(error instanceof Error ? error.message : "Falha ao exportar.");
    }
  };

  const onImportFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    let data: unknown;
    try {
      data = JSON.parse(await file.text());
    } catch {
      showToast("Arquivo não é um JSON válido.");
      return;
    }
    apply((c) => importProfiles(c, data)); // erros (perfil inválido) viram toast
  };

  if (!config) return null;
  const profiles = config.profiles ?? [];
  const active = profiles.find((p) => p.id === config.active_profile) ?? profiles[0];
  const pages = active?.pages ?? [];
  const activePage = pages[Math.min(activePageIndex, Math.max(pages.length - 1, 0))];

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
    onExport?: () => void,
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
            {onExport && rowButton(onExport, "mdi:download-outline")}
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
              () => doExport(profile.id),
            ),
          )}
          <AddRow
            placeholder="Novo perfil…"
            onAdd={(name) => {
              apply((c) => addProfile(c, name));
              setPage(0);
            }}
          />
          <button
            type="button"
            onClick={() => importRef.current?.click()}
            className="flex items-center justify-center gap-2 rounded-xl bg-slate-800/70 px-3 py-2 text-sm text-slate-200 active:bg-slate-700"
          >
            <Icon icon="mdi:file-upload-outline" style={{ fontSize: "1.1rem" }} />
            Importar perfil
          </button>
          <input
            ref={importRef}
            type="file"
            accept="application/json,.json"
            className="hidden"
            onChange={onImportFile}
          />
          <p className="text-[11px] leading-relaxed text-slate-500">
            Exportar (↓) salva o perfil num arquivo JSON; importar soma esse perfil aos seus,
            com nomes/ids novos. Bom para backup ou levar a config para outro PC.
          </p>
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

        {activePage && (
          <section className="flex flex-col gap-2">
            <h3 className="text-xs font-semibold tracking-wide text-slate-500 uppercase">
              Grade — “{activePage.name}”
            </h3>
            <Stepper
              label="Colunas"
              value={activePage.grid?.cols ?? 3}
              min={GRID_LIMITS.cols.min}
              max={GRID_LIMITS.cols.max}
              onChange={(v) => apply((c) => setGrid(c, active.id, activePage.id, { cols: v }))}
            />
            <Stepper
              label="Linhas"
              value={activePage.grid?.rows ?? 4}
              min={GRID_LIMITS.rows.min}
              max={GRID_LIMITS.rows.max}
              onChange={(v) => apply((c) => setGrid(c, active.id, activePage.id, { rows: v }))}
            />
            <button
              type="button"
              onClick={() => apply((c) => repackButtons(c, active.id, activePage.id))}
              className="flex items-center justify-center gap-2 rounded-xl bg-slate-800/70 px-3 py-2 text-sm text-slate-200 active:bg-slate-700"
            >
              <Icon icon="mdi:view-grid-plus-outline" style={{ fontSize: "1.1rem" }} />
              Reorganizar botões
            </button>
            <p className="text-[11px] leading-relaxed text-slate-500">
              Vale para esta página. Os botões preenchem a tela — menos colunas/linhas deixa cada
              botão maior. Para o celular deitado, mais colunas aproveitam a largura; toque em
              “Reorganizar” para distribuir os botões sem buracos.
            </p>
          </section>
        )}

        <section className="flex flex-col gap-2">
          <h3 className="text-xs font-semibold tracking-wide text-slate-500 uppercase">
            Perfil automático
          </h3>
          <p className="text-[11px] leading-relaxed text-slate-500">
            Troca o perfil sozinho quando a janela em foco no PC combina (só em X11). Ex.:
            “code” → Dev. Confere a classe ou o título da janela.
          </p>
          {(config.auto_profile ?? []).map((rule, index) => (
            <div
              key={`${rule.match}:${index}`}
              className="flex items-center gap-2 rounded-xl bg-slate-800/70 px-3 py-1.5"
            >
              <span className="flex-1 truncate text-sm text-slate-200">
                <span className="text-slate-500">contém</span> “{rule.match}”{" "}
                <span className="text-slate-500">→</span>{" "}
                {profiles.find((p) => p.id === rule.profile)?.name ?? rule.profile}
              </span>
              {rowButton(
                () => apply((c) => removeAutoRule(c, index)),
                "mdi:trash-can-outline",
                true,
              )}
            </div>
          ))}
          <AutoRuleAdd
            profiles={profiles.map((p) => ({ id: p.id, name: p.name }))}
            onAdd={(match, profile) => apply((c) => addAutoRule(c, match, profile))}
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

function AutoRuleAdd({
  profiles,
  onAdd,
}: {
  profiles: { id: string; name: string }[];
  onAdd: (match: string, profile: string) => void;
}) {
  const [match, setMatch] = useState("");
  const [profile, setProfile] = useState(profiles[0]?.id ?? "");
  const add = () => {
    if (!match.trim() || !profile) return;
    onAdd(match, profile);
    setMatch("");
  };
  return (
    <div className="flex items-center gap-1.5">
      <input
        className={inputClass}
        value={match}
        onChange={(e) => setMatch(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && add()}
        placeholder="janela contém… (ex.: code)"
      />
      <select
        className={`${inputClass} w-28 shrink-0`}
        value={profile}
        onChange={(e) => setProfile(e.target.value)}
      >
        {profiles.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name}
          </option>
        ))}
      </select>
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

function Stepper({
  label,
  value,
  min,
  max,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  onChange: (value: number) => void;
}) {
  const step = (delta: number) => {
    const next = value + delta;
    if (next >= min && next <= max) onChange(next);
  };
  const btn =
    "flex h-7 w-7 items-center justify-center rounded-lg bg-slate-700 text-slate-200 disabled:opacity-40 active:bg-slate-600";
  return (
    <div className="flex items-center justify-between rounded-xl bg-slate-800/70 px-3 py-2">
      <span className="text-sm text-slate-200">{label}</span>
      <div className="flex items-center gap-3">
        <button type="button" aria-label={`Menos ${label}`} disabled={value <= min} onClick={() => step(-1)} className={btn}>
          <Icon icon="mdi:minus" style={{ fontSize: "1rem" }} />
        </button>
        <span className="w-5 text-center text-sm font-semibold text-slate-100 tabular-nums">
          {value}
        </span>
        <button type="button" aria-label={`Mais ${label}`} disabled={value >= max} onClick={() => step(1)} className={btn}>
          <Icon icon="mdi:plus" style={{ fontSize: "1rem" }} />
        </button>
      </div>
    </div>
  );
}
