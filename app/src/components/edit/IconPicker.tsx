import { Icon } from "@iconify/react";
import { useEffect, useRef, useState, type ChangeEvent } from "react";

import { ButtonIcon } from "../ButtonIcon";
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

/** Lê um arquivo de imagem e devolve uma data URL PNG de 128px (cabe no JSON). */
async function fileToIconDataUrl(file: File): Promise<string> {
  const url = URL.createObjectURL(file);
  try {
    const img = await new Promise<HTMLImageElement>((resolve, reject) => {
      const el = new Image();
      el.onload = () => resolve(el);
      el.onerror = () => reject(new Error("imagem inválida"));
      el.src = url;
    });
    const size = 128;
    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = size;
    const ctx = canvas.getContext("2d");
    if (!ctx) return url;
    const scale = Math.min(size / img.width, size / img.height) || 1;
    const w = img.width * scale;
    const h = img.height * scale;
    ctx.drawImage(img, (size - w) / 2, (size - h) / 2, w, h);
    return canvas.toDataURL("image/png");
  } finally {
    URL.revokeObjectURL(url);
  }
}

export function IconPicker({
  value,
  onChange,
}: {
  value: string;
  onChange: (icon: string) => void;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<string[]>(POPULAR);
  const fileRef = useRef<HTMLInputElement>(null);

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

  const onFile = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    try {
      onChange(await fileToIconDataUrl(file));
    } catch {
      // arquivo inválido — ignora
    }
  };

  const isImage = value.startsWith("data:") || value.startsWith("http");

  return (
    <div>
      <label className={labelClass}>Ícone</label>
      <div className="flex gap-1.5">
        <input
          className={inputClass}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Buscar (ex.: terminal, git, spotify…)"
        />
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          title="Usar uma imagem do PC (ex.: o ícone de um programa)"
          className="flex shrink-0 items-center gap-1.5 rounded-xl bg-slate-800 px-3 text-sm font-medium text-slate-300 active:bg-slate-700"
        >
          <Icon icon="mdi:image-plus-outline" style={{ fontSize: "1.15rem" }} />
          Imagem
        </button>
        <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={onFile} />
      </div>
      <div className="mt-2 grid max-h-36 grid-cols-7 gap-1.5 overflow-y-auto">
        {isImage && (
          <button
            type="button"
            title="imagem escolhida"
            className="flex aspect-square items-center justify-center rounded-lg bg-blue-600 p-1.5"
          >
            <ButtonIcon icon={value} size="1.6rem" />
          </button>
        )}
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
      <p className="mt-1 text-[11px] text-slate-500">
        “Imagem” usa um arquivo do PC (PNG/SVG) — ex.: o ícone do VS Code. Configurando pelo
        navegador do computador você acha a pasta do app no seletor.
      </p>
    </div>
  );
}
