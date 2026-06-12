import { Icon } from "@iconify/react";
import { useEffect, useState } from "react";

import { inputClass, labelClass } from "./Sheet";

const POPULAR = [
  "mdi:folder",
  "mdi:folder-download",
  "mdi:microsoft-visual-studio-code",
  "mdi:github",
  "mdi:console",
  "mdi:rocket-launch",
  "mdi:web",
  "mdi:lock",
  "mdi:camera",
  "mdi:play",
  "mdi:volume-high",
  "mdi:email",
  "mdi:calendar",
  "mdi:music",
  "mdi:docker",
  "mdi:spotify",
  "mdi:youtube",
  "mdi:home",
  "mdi:cog",
  "mdi:lightning-bolt",
  "mdi:microphone-off",
];

export function IconPicker({
  value,
  onChange,
}: {
  value: string;
  onChange: (icon: string) => void;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<string[]>(POPULAR);

  useEffect(() => {
    const q = query.trim();
    if (!q) {
      setResults(POPULAR);
      return;
    }
    const timer = window.setTimeout(async () => {
      try {
        const res = await fetch(
          `https://api.iconify.design/search?query=${encodeURIComponent(q)}&limit=42`,
        );
        const data = (await res.json()) as { icons?: string[] };
        let icons = data.icons ?? [];
        // nome exato "prefixo:icone" sempre é uma opção, mesmo fora da busca
        if (q.includes(":") && !icons.includes(q)) icons = [q, ...icons];
        setResults(icons);
      } catch {
        // sem internet: aceita apenas o nome exato
        setResults(q.includes(":") ? [q] : []);
      }
    }, 300);
    return () => window.clearTimeout(timer);
  }, [query]);

  return (
    <div>
      <label className={labelClass}>Ícone</label>
      <input
        className={inputClass}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Buscar (ex.: terminal, git, spotify…)"
      />
      <div className="mt-2 grid max-h-36 grid-cols-7 gap-1.5 overflow-y-auto">
        {results.map((icon) => (
          <button
            key={icon}
            type="button"
            onClick={() => onChange(icon)}
            title={icon}
            className={`flex aspect-square items-center justify-center rounded-lg text-slate-200 transition-colors ${
              icon === value ? "bg-blue-600" : "bg-slate-800 active:bg-slate-700"
            }`}
          >
            <Icon icon={icon} style={{ fontSize: "1.3rem" }} />
          </button>
        ))}
        {results.length === 0 && (
          <p className="col-span-7 py-3 text-center text-xs text-slate-500">
            Nada encontrado — digite o nome exato (ex.: mdi:folder)
          </p>
        )}
      </div>
    </div>
  );
}
