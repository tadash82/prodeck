import { useEffect, useState } from "react";

import { token } from "../../lib/identity";
import { inputClass, labelClass } from "./Sheet";

export type PluginMeta = {
  name: string;
  label: string;
  icon: string;
  color: string;
  fields: { key: string; label: string; placeholder: string }[];
};

/** Ações vindas de plugins (pacotes Python com entry point prodeck.actions).
 * Lista os plugins do agente (`/plugins`) e renderiza os campos de cada um
 * dinamicamente — o front não sabe de antemão quais ações existem. */
export function PluginEditor({
  name,
  params,
  onChange,
  onSelect,
}: {
  name: string;
  params: Record<string, string>;
  onChange: (name: string, params: Record<string, string>) => void;
  onSelect: (meta: PluginMeta) => void;
}) {
  const [plugins, setPlugins] = useState<PluginMeta[] | null>(null);

  useEffect(() => {
    fetch(`/plugins?token=${encodeURIComponent(token() ?? "")}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((data: PluginMeta[]) => setPlugins(data))
      .catch(() => setPlugins([]));
  }, []);

  if (plugins === null) {
    return <p className="text-[11px] text-slate-500">Carregando plugins…</p>;
  }
  if (plugins.length === 0) {
    return (
      <p className="text-[11px] leading-relaxed text-slate-500">
        Nenhum plugin instalado. Plugins são pacotes Python que registram ações novas
        pelo entry point <code className="text-slate-400">prodeck.actions</code>.
      </p>
    );
  }

  const current = plugins.find((p) => p.name === name) ?? null;

  return (
    <div className="flex flex-col gap-2">
      <div>
        <label className={labelClass}>Plugin</label>
        <select
          className={inputClass}
          value={name}
          onChange={(e) => {
            const meta = plugins.find((p) => p.name === e.target.value);
            if (!meta) {
              onChange("", {});
              return;
            }
            onChange(meta.name, {}); // troca de plugin zera os campos
            onSelect(meta);
          }}
        >
          <option value="">Escolha um plugin…</option>
          {plugins.map((p) => (
            <option key={p.name} value={p.name}>
              {p.label}
            </option>
          ))}
        </select>
      </div>
      {current?.fields.map((f) => (
        <div key={f.key}>
          <label className={labelClass}>{f.label}</label>
          <input
            className={inputClass}
            value={params[f.key] ?? ""}
            onChange={(e) => onChange(name, { ...params, [f.key]: e.target.value })}
            placeholder={f.placeholder}
          />
        </div>
      ))}
    </div>
  );
}
